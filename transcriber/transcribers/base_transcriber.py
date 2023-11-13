from abc import ABC, abstractmethod
from rest_framework import exceptions


class BaseTranscriber(ABC):
    @property
    @abstractmethod
    def supported_filetypes() -> list[str]:
        ...

    @abstractmethod
    def transcribe(self, filepath: str, filetype: str) -> str:
        ...

    def check_filetype(self, filetype):
        if filetype not in self.supported_filetypes:
            raise exceptions.ValidationError(
                f'Filetype {filetype} not supported. '
                f'Supported file types are {self.supported_filetypes}.'
            )