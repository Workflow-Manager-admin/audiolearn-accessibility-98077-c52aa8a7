# AudioLearn Accessible English Backend – API Documentation

This document describes the RESTful API endpoints implemented in the backend (`backend_api/src/api/main.py`) using FastAPI. It details each route, HTTP method, path, parameters, expected requests and responses, and relevant usage notes. Schemas are described as used in the actual implementation.

---

## Table of Contents

- [Health Check](#health-check)
- [User Endpoints](#user-endpoints)
- [Content Endpoints](#content-endpoints)
- [Favorites & Daily Suggestions](#favorites--daily-suggestions)
- [TTS (Text-to-Speech) Endpoints](#tts-text-to-speech-endpoints)
- [Quiz Endpoints](#quiz-endpoints)
- [Voice Command Interface](#voice-command-interface)
- [Offline Export](#offline-export)
- [WebSocket/Voice Command Usage Help](#websocketvoice-command-usage-help)
- [Schemas](#schemas)

---

## Health Check

### GET `/`

**Summary:** System health check.  
**Response:**
```json
{ "status": "Healthy" }
```

---

## User Endpoints

### POST `/users/`

- **Summary:** Register new user
- **Request body:** [`UserCreate`](#schemas)
- **Response:** [`UserOut`](#schemas)
- **Errors:** 400 if username already exists

**Example request**
```json
POST /users/
{
  "username": "alice",
  "preferred_font_size": 22,
  "preferred_tts_speed": 1.2,
  "preferred_language": "en"
}
```
**Example response**
```json
{
  "username": "alice",
  "preferred_font_size": 22,
  "preferred_tts_speed": 1.2,
  "preferred_language": "en",
  "id": 1
}
```

---

### GET `/users/{user_id}`

- **Summary:** Get user info
- **Path parameter:** `user_id` (integer)
- **Response:** [`UserOut`](#schemas)
- **Errors:** 404 if not found

---

### PUT `/users/{user_id}/preferences`

- **Summary:** Update user preferences
- **Path parameter:** `user_id` (integer)
- **Request body:** [`UserCreate`](#schemas)
- **Response:** [`UserOut`](#schemas)
- **Errors:** 404 if not found

---

### GET `/export/userdata/{user_id}`

- **Summary:** Export user data (for offline access)
- **Path parameter:** `user_id` (integer)
- **Response:** User object, favorites, and quiz results for offline caching

---

## Content Endpoints

### POST `/content/`

- **Summary:** Add new learning content
- **Request body:** [`ContentBase`](#schemas)
- **Response:** [`ContentOut`](#schemas)

---

### GET `/content/`

- **Summary:** List content
- **Query parameters (optional):**
  - `type`: 'word' | 'sentence' | 'paragraph'
  - `language`: language code (e.g., 'en', 'ta', 'hi')
- **Response:** Array of [`ContentOut`](#schemas)

---

### GET `/content/{content_id}`

- **Summary:** Get content by ID
- **Path parameter:** `content_id` (integer)
- **Response:** [`ContentOut`](#schemas)
- **Errors:** 404 if not found

---

## Favorites & Daily Suggestions

### POST `/favorites/`

- **Summary:** Add favorite
- **Query parameters:** `user_id` (integer), `content_id` (integer)
- **Response:** [`FavoriteOut`](#schemas)

---

### GET `/favorites/{user_id}`

- **Summary:** List user's favorites
- **Path parameter:** `user_id` (integer)
- **Response:** Array of [`ContentOut`](#schemas)

---

### GET `/daily_suggestion/{user_id}`

- **Summary:** Get daily suggestion (random non-favorited content for user)
- **Path parameter:** `user_id` (integer)
- **Response:** 
```json
{ "suggestion": ContentOut }
```
- **Errors:** 404 if no candidates

---

## TTS (Text-to-Speech) Endpoints

### GET `/tts/{content_id}`

- **Summary:** Get TTS audio for content ID (stubbed for demo)
- **Path parameter:** `content_id` (integer)
- **Response:**
```json
{
  "text": "example content text",
  "tts_audio": "TTS_AUDIO_STUB_FOR_ID_123"
}
```
- **Errors:** 404 if not found

---

### POST `/tts/batch`

- **Summary:** Get batch TTS for multiple content IDs (stubbed)
- **Request body:** 
```json
{ "content_ids": [123, 124] }
```
- **Response:**
```json
[
  { "text": "...", "tts_audio": "TTS_AUDIO_STUB_FOR_ID_123" },
  { "text": "...", "tts_audio": "TTS_AUDIO_STUB_FOR_ID_124" }
]
```

---

### GET `/tts/check-db`

- **Summary:** DB TTS check endpoint—fetches a random sample text and (stubbed) audio
- **Response:** [`TTSTestResponse`](#schemas)
- **Errors:** 404 if no content in DB

---

## Quiz Endpoints

### POST `/quiz/`

- **Summary:** Create a quiz question
- **Request body:** [`QuizCreate`](#schemas)
- **Response:** [`QuizOut`](#schemas)

---

### GET `/quiz/`

- **Summary:** List quizzes
- **Query parameter (optional):** `language`
- **Response:** Array of [`QuizOut`](#schemas)

---

### GET `/quiz/{quiz_id}`

- **Summary:** Get quiz by ID
- **Path parameter:** `quiz_id` (integer)
- **Response:** [`QuizOut`](#schemas)

---

### POST `/quiz/results`

- **Summary:** Submit quiz result
- **Request body:** [`QuizResultCreate`](#schemas)
- **Response:** [`QuizResultOut`](#schemas)

---

### GET `/quiz/results/{user_id}`

- **Summary:** List user quiz results
- **Path parameter:** `user_id` (integer)
- **Response:** Array of [`QuizResultOut`](#schemas)

---

## Voice Command Interface

### POST `/voice/command`

- **Summary:** Voice command interface (structure only, stub)
- **Request body:** [`VoiceCommandRequest`](#schemas)
- **Response:**
```json
{
  "recognized_command": "go_to_quiz",
  "context": null,
  "action": "Not implemented - client should handle navigation"
}
```
- **Note:** Only structure is present—actual voice handling is not implemented.

---

## WebSocket/Voice Command Usage Help

### GET `/websocket-usage`

- **Summary:** WebSocket/voice command usage help
- **Response:**
```json
{
  "websocket_url": "<not-implemented>",
  "note": "Voice navigation is currently structure/stub only; real-time features would use /voice/command or a websocket route."
}
```

---

## Schemas

### UserCreate
```json
{
  "username": "string",
  "preferred_font_size": 18,
  "preferred_tts_speed": 1.0,
  "preferred_language": "en"
}
```
### UserOut
`UserCreate` plus:
```json
{
  "id": 1
}
```
### ContentBase
```json
{
  "type": "word",
  "text": "string",
  "language": "en",
  "translation": "string (optional)",
  "audio_url": "string (optional)"
}
```
### ContentOut
`ContentBase` plus:
```json
{
  "id": 100
}
```
### FavoriteOut
```json
{
  "id": 5,
  "user_id": 1,
  "content_id": 100
}
```
### QuizCreate
```json
{
  "content_id": 100,
  "question": "string",
  "correct_answer": "string",
  "distractors": ["string"],
  "language": "en"
}
```
### QuizOut
`QuizCreate` plus:
```json
{
  "id": 50
}
```
### QuizResultCreate
```json
{
  "user_id": 1,
  "quiz_id": 50,
  "score": 4
}
```
### QuizResultOut
`QuizResultCreate` plus:
```json
{
  "id": 1,
  "timestamp": "YYYY-MM-DD HH:mm:ss"
}
```
### DailySuggestionOut
```json
{
  "suggestion": ContentOut
}
```
### VoiceCommandRequest
```json
{
  "command": "string",
  "context": { "key": "value" }
}
```
### TTSTestResponse
```json
{
  "text": "string",
  "tts_audio": "string"
}
```

---

This documentation reflects all currently implemented routes and behaviors as of this codebase revision. Please refer to the FastAPI `/docs` endpoint for live OpenAPI/Swagger visualization.

