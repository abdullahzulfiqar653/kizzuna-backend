from contextlib import contextmanager
from decimal import Decimal

from langchain.callbacks import get_openai_callback

from api.models.usage.token import TokenUsage


@contextmanager
def token_tracker(project, content_object, action, created_by):
    with get_openai_callback() as callback:
        try:
            yield callback
        except Exception as e:
            import traceback

            traceback.print_exc()
            raise e
        finally:
            TokenUsage.objects.create(
                workspace=project.workspace,
                project=project,
                content_object=content_object,
                action=action,
                created_by=created_by,
                value=callback.total_tokens,
                cost=Decimal(callback.total_cost),
            )
