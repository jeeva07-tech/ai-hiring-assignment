from django.urls import path

from .views import PeopleSearchView, CandidateListView


urlpatterns = [
    path("search/", PeopleSearchView.as_view(), name="people-search"),
    path("list/", CandidateListView.as_view(), name="candidate-list"),
]