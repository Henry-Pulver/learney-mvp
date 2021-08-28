import datetime
import time
from pathlib import Path

from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

import boto3
from knowledge_maps.models import KnowledgeMapModel
from knowledge_maps.serializers import KnowledgeMapSerializer
from learney_web.settings import AWS_CREDENTIALS

S3_CACHE_DIR = Path("S3_cache_dir")


def get_cache_file_location(knowledge_map_model: KnowledgeMapModel) -> Path:
    s3_key_filename = Path(knowledge_map_model.s3_key)
    filename = f"{s3_key_filename.stem}_{knowledge_map_model.version}.{s3_key_filename.suffix}"
    return S3_CACHE_DIR / knowledge_map_model.s3_bucket_name / filename


def retrieve_map_from_s3(knowledge_map_db_entry: KnowledgeMapModel) -> bytes:
    """Check local file first, then get it from S3 if tricky."""
    cache_file_location = get_cache_file_location(knowledge_map_db_entry)

    if cache_file_location.exists():
        with cache_file_location.open("r") as cache_file:
            read_cache_file = cache_file.read()
        return bytes(read_cache_file, "utf-8")
    else:
        s3 = boto3.resource(
            "s3",
            aws_access_key_id=AWS_CREDENTIALS["ACCESS_ID"],
            aws_secret_access_key=AWS_CREDENTIALS["SECRET_KEY"],
        )
        response = s3.Object(
            knowledge_map_db_entry.s3_bucket_name, knowledge_map_db_entry.s3_key
        ).get()
        map_byte_str = response["Body"].read()
        cache_file_location.parent.mkdir(exist_ok=True, parents=True)
        with cache_file_location.open("w") as cache_file:
            cache_file.write(map_byte_str.decode("utf-8"))
        return map_byte_str


class KnowledgeMapView(APIView):
    def get(self, request: Request, format=None):
        try:
            entry = KnowledgeMapModel.objects.filter(
                unique_id=request.GET["map_uuid"], version=int(request.GET["version"])
            ).latest("last_updated")
            return Response(retrieve_map_from_s3(entry), status=status.HTTP_200_OK)
        except ObjectDoesNotExist as error:
            return Response(error, status=status.HTTP_204_NO_CONTENT)

    def post(self, request: Request, format=None):
        serializer = KnowledgeMapSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request: Request, format=None):
        # TODO: Write test for this view!
        try:
            entry = KnowledgeMapModel.objects.filter(unique_id=request.PUT["map_uuid"]).latest(
                "last_updated"
            )
            entry.version += 1
            entry.s3_bucket_name = request.PUT.get("s3_bucket_name", entry.s3_bucket_name)
            entry.s3_key = request.PUT.get("s3_key", entry.s3_key)
            serializer = KnowledgeMapSerializer(entry)
            return Response(serializer, status=status.HTTP_200_OK)
        except MultiValueDictKeyError as e:
            return Response(
                f"Invalid request: {request.PUT}\n\n{e}", status=status.HTTP_400_BAD_REQUEST
            )
