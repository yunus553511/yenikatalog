# Requirements Document

## Introduction

Bu özellik, mevcut RAG sistemine Groq LLM entegrasyonu ekleyerek kullanıcı sorularına daha doğal, açıklayıcı ve bağlam-farkında cevaplar üretmeyi sağlar. Mevcut profil arama ve filtreleme mantığı korunacak, LLM sadece cevap formatlamada kullanılacaktır.

## Glossary

- **System**: Beymetal Chat Backend API
- **LLM**: Large Language Model (Groq API üzerinden Llama 3.1 70B)
- **RAG Service**: Mevcut Retrieval-Augmented Generation servisi
- **User**: Sistem kullanıcısı (profil arayan kişi)
- **Profile**: Alüminyum profil ürünü
- **Context**: LLM'e gönderilen profil bilgileri
- **Groq API**: Groq'un LLM API servisi
- **Rate Limit**: API kullanım limiti (30 request/dakika)

## Requirements

### Requirement 1

**User Story:** As a user, I want to ask questions in natural language, so that I can get conversational responses about aluminum profiles

#### Acceptance Criteria

1. WHEN the User sends a chat message, THE System SHALL use the existing RAG service to retrieve relevant profiles
2. WHEN relevant profiles are found, THE System SHALL send the profiles and user query to Groq LLM
3. WHEN Groq LLM returns a response, THE System SHALL return the formatted answer to the User
4. WHEN no profiles are found, THE System SHALL return a helpful message without calling the LLM
5. WHEN the User query is in Turkish, THE System SHALL maintain Turkish language in the response

### Requirement 2

**User Story:** As a developer, I want to configure Groq API credentials securely, so that the API key is not exposed in code

#### Acceptance Criteria

1. THE System SHALL read Groq API key from environment variables
2. THE System SHALL validate the API key exists before making requests
3. WHEN the API key is missing, THE System SHALL log an error and fall back to direct answers
4. THE System SHALL store the API configuration in the config module
5. THE System SHALL NOT expose the API key in logs or error messages

### Requirement 3

**User Story:** As a system administrator, I want the system to handle Groq API rate limits gracefully, so that users get responses even during high traffic

#### Acceptance Criteria

1. WHEN Groq API returns a rate limit error (429), THE System SHALL fall back to direct answer format
2. WHEN Groq API is unavailable, THE System SHALL fall back to direct answer format
3. WHEN a fallback occurs, THE System SHALL log the reason for monitoring
4. THE System SHALL set a timeout of 10 seconds for LLM requests
5. WHEN timeout occurs, THE System SHALL return a direct answer without LLM

### Requirement 4

**User Story:** As a user, I want the LLM to understand context from previous messages, so that I can have multi-turn conversations

#### Acceptance Criteria

1. WHEN the User sends conversation history from the frontend, THE System SHALL pass it directly to the LLM
2. THE System SHALL accept conversation history in OpenAI-compatible message format (role, content)
3. WHEN conversation history is provided, THE System SHALL preserve all messages including tool calls and tool responses
4. THE System SHALL NOT modify or filter conversation history before sending to LLM
5. THE System SHALL allow the frontend to manage conversation history length and token limits

### Requirement 5

**User Story:** As a developer, I want to monitor LLM usage and performance, so that I can optimize costs and response times

#### Acceptance Criteria

1. THE System SHALL log the number of tokens used in each LLM request
2. THE System SHALL log the response time for each LLM call
3. THE System SHALL log whether LLM was used or fallback occurred
4. THE System SHALL include LLM usage statistics in the chat response
5. WHEN an error occurs, THE System SHALL log the error details for debugging

### Requirement 6

**User Story:** As a user, I want the LLM to provide accurate information based only on retrieved profiles, so that I don't receive hallucinated or incorrect data

#### Acceptance Criteria

1. THE System SHALL include a system prompt that instructs the LLM to only use provided profile data
2. THE System SHALL instruct the LLM to not make up profile codes or specifications
3. WHEN the LLM cannot answer from the context, THE System SHALL instruct it to say so clearly
4. THE System SHALL format profile context in a clear, structured way for the LLM
5. THE System SHALL include profile images URLs in the context when available

### Requirement 7

**User Story:** As a developer, I want to easily switch between different LLM models, so that I can test and optimize performance

#### Acceptance Criteria

1. THE System SHALL allow configuring the LLM model name via environment variables
2. THE System SHALL default to "llama-3.1-70b-versatile" model
3. THE System SHALL support alternative models like "llama-3.1-8b-instant"
4. WHEN an unsupported model is configured, THE System SHALL log a warning and use the default
5. THE System SHALL allow configuring temperature and max_tokens parameters

### Requirement 8

**User Story:** As a user, I want the AI to manage the entire conversation flow and remember context, so that I can have natural multi-turn conversations without repeating information

#### Acceptance Criteria

1. THE System SHALL use the LLM as the primary conversation manager that maintains full conversation history
2. WHEN the LLM determines it needs profile information, THE System SHALL provide a tool/function that the LLM can call
3. THE System SHALL define a "search_profiles" tool that the LLM can invoke with user requirements
4. WHEN the LLM calls the search_profiles tool, THE System SHALL execute the RAG service and return results to the LLM
5. THE System SHALL allow the LLM to make multiple tool calls in a single conversation turn if needed
6. WHEN the LLM receives tool results, THE System SHALL allow it to formulate the final response to the user
7. THE System SHALL maintain conversation history on the LLM side, not in the backend API
8. WHEN the user sends a follow-up question, THE System SHALL send the full conversation history to the LLM
9. THE System SHALL NOT manage conversation state in the backend - the LLM manages all context
10. THE System SHALL support Groq's function calling format for tool definitions
