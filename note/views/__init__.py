from .note import NoteRetrieveUpdateDeleteView
from .note_keyword import NoteKeywordDestroyView, NoteKeywordListCreateView
from .note_tag import NoteTagListView
from .note_tag_generate import NoteTagGenerateView
from .note_takeaway import NoteTakeawayListCreateView

__all__ = [
    NoteRetrieveUpdateDeleteView,
    NoteKeywordDestroyView,
    NoteKeywordListCreateView,
    NoteTagGenerateView,
    NoteTakeawayListCreateView,
    NoteTagListView,
]
