from typing import Any, Dict
from uuid import UUID, uuid4

from django.core.cache import cache

from accounts.models import User
from questions.models import QuestionResponse
from questions.models.question_batch import QuestionBatch


class QuestionBatchCacheManager:
    """Manages the cache for question batches.

    This is required because of the asynchronous nature of the frontend.
    """

    STALE = "stale"

    def __init__(self, question_batch_id: UUID):
        self.question_batch_id = question_batch_id
        self._q_batch_json: Dict[str, Any] = {}

        self.q_batch: QuestionBatch = cache.get(question_batch_id)
        if self.q_batch is None:
            self.q_batch = (
                QuestionBatch.objects.prefetch_related("user__knowledge_states__concept")
                .prefetch_related("responses__question_template__concept")
                .get(id=question_batch_id)
            )
            cache.set(question_batch_id, self.q_batch, timeout=1200)

        # Get all the precomputed json data from the cache
        self._q_batch_json = cache.get(self._batch_json_key)
        # And redo the computations now if it's not there!
        if self._q_batch_json is None:
            self._q_batch_json = self.q_batch.json()
            self._set_cache()

        # Get the id of the question batch from the cache
        current_cache_update_id = cache.get(self._memory_stale_key)
        self._cache_update_id = (
            current_cache_update_id if current_cache_update_id is not None else uuid4()
        )
        if current_cache_update_id is None:
            cache.set(self._memory_stale_key, self._cache_update_id, timeout=10)

    @property
    def _memory_stale_key(self) -> str:
        return f"Stale:{self.q_batch.id}"

    @property
    def _batch_json_key(self) -> str:
        return f"question_json:{self.question_batch_id}"

    @property
    def q_batch_json(self) -> Dict[str, Any]:
        self._ensure_memory_fresh()
        return self._q_batch_json

    @property
    def batch_id(self) -> str:
        return self._q_batch_json["id"]

    @property
    def concept_id(self) -> str:
        return self._q_batch_json["concept_id"]

    @property
    def user(self) -> User:
        return self.q_batch.user

    @property
    def max_num_questions(self) -> int:
        return self._q_batch_json["max_num_questions"]

    def add_question_asked(self, question_json: Dict[str, Any]):
        print(f"Adding question asked {question_json['id']}")
        self._ensure_memory_fresh()
        self._q_batch_json["questions"].append(question_json)
        self._set_cache()

    def add_question_answered(self, q_response: QuestionResponse):
        print(f"Adding question answered {q_response.id}")
        self._ensure_memory_fresh()
        self._q_batch_json["answers_given"][str(q_response.id)] = q_response.response
        self._set_cache()

    def _ensure_memory_fresh(self) -> None:
        """If the memory is stale, reload it from the cache and set self._cache_update_id to the new
        id in cache."""
        new_cache_update_id = cache.get(self._memory_stale_key)
        if new_cache_update_id != self._cache_update_id:
            print("memory stale!")
            self._q_batch_json = cache.get(self._batch_json_key)
            # Update to the new cache id with the new data
            self._cache_update_id = new_cache_update_id

    def _set_memory_stale(self):
        print("Setting memory stale")
        self._cache_update_id = uuid4()
        cache.set(self._memory_stale_key, self._cache_update_id, 10)

    def _set_cache(self):
        self._set_memory_stale()
        cache.set(self._batch_json_key, self._q_batch_json, timeout=1200)
