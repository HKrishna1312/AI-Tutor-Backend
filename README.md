# AI-Tutor-Backend
consists of API files 

## Completed interview processing API

All interview endpoints require `Authorization: Bearer <access_token>`.

- `POST /interviews/process` accepts the completed LiveKit transcript, pairs assistant questions with candidate answers, stores the complete interview, and returns scores, concepts from weakest to strongest, and focus areas.
