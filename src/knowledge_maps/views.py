import json
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
from learney_web.settings import AWS_CREDENTIALS, IS_PROD, mixpanel
from learney_web.utils import S3_CACHE_DIR, retrieve_map_from_s3


def get_cache_file_location(knowledge_map_model: KnowledgeMapModel) -> Path:
    s3_key_filename = Path(knowledge_map_model.s3_key)
    filename = f"{s3_key_filename.stem}_{knowledge_map_model.version}{s3_key_filename.suffix}"
    return S3_CACHE_DIR / knowledge_map_model.s3_bucket_name / filename


def retrieve_map(knowledge_map_db_entry: KnowledgeMapModel) -> bytes:
    """Check local file first, then get it from S3 if tricky."""
    cache_file_location = get_cache_file_location(knowledge_map_db_entry)

    if cache_file_location.exists():
        with cache_file_location.open("r") as cache_file:
            read_cache_file = cache_file.read()
        return bytes(read_cache_file, "utf-8")
    else:
        map_byte_str = retrieve_map_from_s3(
            knowledge_map_db_entry.s3_bucket_name, knowledge_map_db_entry.s3_key, AWS_CREDENTIALS
        )
        cache_file_location.parent.mkdir(exist_ok=True, parents=True)
        with cache_file_location.open("w") as cache_file:
            cache_file.write(map_byte_str.decode("utf-8"))
        return map_byte_str


class KnowledgeMapView(APIView):
    def get(self, request: Request, format=None):
        try:
            if "url_extension" in request.GET:
                entry = KnowledgeMapModel.objects.get(url_extension=request.GET["url_extension"])
                serializer = KnowledgeMapSerializer(entry)
                return Response(
                    {**serializer.data, "map_json": entry.retrieve_map()}, status=status.HTTP_200_OK
                )
            elif "map" in request.GET:
                entry = KnowledgeMapModel.objects.get(unique_id=request.GET["map"])
                return Response(
                    {
                        "map_json": entry.retrieve_map(),
                        "map": entry.unique_id,
                        "allow_suggestions": entry.allow_suggestions,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    KnowledgeMapModel.objects.values_list("url_extension", flat=True),
                    status=status.HTTP_200_OK,
                )

        except ObjectDoesNotExist as error:
            return Response(str(error), status=status.HTTP_204_NO_CONTENT)
        except MultiValueDictKeyError as e:
            return Response(
                f"Invalid request: {request.POST}\n\n{e}", status=status.HTTP_400_BAD_REQUEST
            )

    def post(self, request: Request, format=None):
        serializer = KnowledgeMapSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request: Request, format=None):
        # TODO: Write test for this view!
        # TODO: Enable adding maps through this view
        request_body = json.loads(request.body.decode("utf-8"))
        try:
            # {
            #     map: ,
            #     map_data: ,
            #     user_id: ,
            #     s3_key: , (optional)
            #     s3_bucket_name: , (optional)
            # }
            entry = KnowledgeMapModel.objects.get(unique_id=request_body["map"])
            entry.s3_bucket_name = request_body.get("s3_bucket_name", entry.s3_bucket_name)
            entry.s3_key = request_body.get("s3_key", entry.s3_key)
            s3 = boto3.resource(
                "s3",
                aws_access_key_id=AWS_CREDENTIALS["ACCESS_ID"],
                aws_secret_access_key=AWS_CREDENTIALS["SECRET_KEY"],
            )
            s3.Bucket(entry.s3_bucket_name).put_object(
                Key=entry.s3_key, Body=json.dumps(request_body["map_data"])
            )

            entry.version += 1  # Increment the version
            entry.save()
            if IS_PROD:
                mixpanel.track(
                    request_body["user_id"],
                    "Map Save",
                    {
                        "url_extension": entry.url_extension,
                        "Map URL extension": entry.url_extension,
                        "Map Title": entry.title,
                        "map_uuid": request_body["map"],
                        "s3_bucket_name": entry.s3_bucket_name,
                        "new_map_version": entry.version,
                    },
                )
            return Response(KnowledgeMapSerializer(entry).data, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist as error:
            return Response(str(error), status=status.HTTP_204_NO_CONTENT)
        except KeyError as e:
            return Response(
                f"Error: {e}\n\nInvalid request: {request_body}", status=status.HTTP_400_BAD_REQUEST
            )
