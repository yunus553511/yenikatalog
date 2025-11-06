# Implementation Plan

- [x] 1. Setup project configuration and dependencies


  - Add Groq API configuration to config.py (api_key, model, base_url, timeout, temperature, max_tokens, llm_enabled)
  - Add aiohttp dependency to requirements.txt
  - Create .env.example with Groq configuration template
  - _Requirements: 2.1, 2.2, 2.3, 2.4_





- [ ] 2. Implement Groq API client with function calling support
  - [x] 2.1 Create GroqClient class in backend/clients/groq_client.py


    - Implement __init__ with api_key and base_url parameters
    - Create aiohttp ClientSession for async HTTP requests
    - Implement authentication headers
    - _Requirements: 2.1, 2.2_
  
  - [ ] 2.2 Implement chat_completion method with function calling
    - Format request payload for Groq API with tools parameter
    - Support tools (function definitions) and tool_choice parameters
    - Make async POST request to /chat/completions endpoint
    - Parse response and extract message, tool_calls, tokens_used
    - Handle both regular messages and tool call responses
    - Handle HTTP errors (4xx, 5xx)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 8.3, 8.10_
  
  - [ ] 2.3 Implement error handling and timeout
    - Add timeout parameter to requests (10 seconds)
    - Detect rate limit errors (429 status code)
    - Raise appropriate exceptions for different error types
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 2.4 Implement session management
    - Create close() method for cleanup
    - Implement context manager support (__aenter__, __aexit__)
    - _Requirements: 2.1_


- [ ] 3. Create LLM data models for AI-driven architecture
  - [ ] 3.1 Create LLMResponse model in backend/models/llm.py
    - Define fields: message (optional), tool_calls (optional), tokens_used, model_used, fallback_used, error
    - Add Pydantic validation
    - Support both regular responses and tool call responses
    - _Requirements: 5.1, 5.2, 5.3, 8.3, 8.6_
  
  - [ ] 3.2 Update ChatRequest model in backend/models/chat.py
    - Add optional conversation_history field (List[Dict])
    - Support OpenAI-compatible message format (role, content, tool_calls, tool_call_id)
    - _Requirements: 4.1, 4.2, 8.1, 8.7_



  
  - [ ] 3.3 Update ChatResponse model in backend/models/chat.py
    - Add conversation_history field to return updated history to frontend
    - Add optional metadata field for LLM usage stats
    - _Requirements: 5.1, 5.2, 5.4, 8.7, 8.9_

- [ ] 4. Implement LLM service as conversation manager
  - [ ] 4.1 Create LLMService class in backend/services/llm_service.py
    - Implement __init__ with configuration from settings and rag_service reference
    - Initialize GroqClient instance
    - Add is_enabled property based on API key availability
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 8.1_
  
  - [ ] 4.2 Implement system prompt with tool awareness
    - Create SYSTEM_PROMPT constant with Turkish instructions
    - Include tool usage guidelines (when to call search_profiles, when not to)
    - Emphasize conversation history awareness
    - _Requirements: 1.5, 6.1, 6.2, 6.3, 8.1, 8.2_
  
  - [ ] 4.3 Implement tool definitions
    - Create _get_tool_definitions() method returning Groq function calling format
    - Define search_profiles tool with parameters (query, top_k)
    - Add clear descriptions in Turkish for the LLM
    - _Requirements: 8.3, 8.4, 8.10_
  
  - [ ] 4.4 Implement chat method for conversation management
    - Accept messages (full conversation history) and tools parameters
    - Call GroqClient.chat_completion() with function calling support
    - Return LLMResponse with either message or tool_calls
    - Handle both regular responses and tool call requests
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.2, 8.1, 8.6_
  
  - [ ] 4.5 Implement tool execution handler
    - Create handle_tool_calls() method to execute tool calls
    - Parse tool call arguments (JSON)
    - Route to appropriate tool handler (_execute_search_profiles)
    - Format tool results for LLM consumption
    - Return tool results in OpenAI-compatible format
    - _Requirements: 8.3, 8.4, 8.5_
  
  - [ ] 4.6 Implement search_profiles tool handler
    - Create _execute_search_profiles() method
    - Call rag_service to search profiles
    - Format results as structured text for LLM
    - Include profile codes, categories, dimensions, images
    - Handle empty results gracefully
    - _Requirements: 6.4, 6.5, 8.4, 8.5_
  
  - [ ] 4.7 Implement error handling and fallback
    - Catch rate limit errors (429) and return fallback indicator
    - Catch timeout errors and return fallback indicator
    - Catch API errors and return fallback indicator
    - Log all errors with appropriate levels
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 5.3, 5.4_
  
  - [ ] 4.8 Implement usage tracking
    - Create get_stats() method for monitoring
    - Track total requests, successful calls, fallback count
    - Track tool calls made
    - Track average tokens and response time
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 5. Update RAG service to work as a tool
  - [ ] 5.1 Keep existing search methods unchanged
    - Verify search(), search_by_dimension(), search_by_embedding() work as-is
    - These methods will be called by LLMService as tools
    - No changes needed to core search logic
    - _Requirements: 8.4, 8.5_
  
  - [ ] 5.2 Add helper method for tool result formatting
    - Create format_profiles_for_llm() method
    - Format profile list as structured text
    - Include profile codes, categories, dimensions, images
    - Keep format concise to minimize tokens
    - Return empty message if no profiles found
    - _Requirements: 6.4, 6.5, 8.5_

- [ ] 6. Update chat endpoint for AI-driven architecture
  - [ ] 6.1 Modify /api/chat endpoint in main.py
    - Import and initialize LLMService with rag_service reference
    - Accept conversation_history from ChatRequest
    - Build messages array (add system prompt if first message, otherwise use history)
    - Append new user message to messages
    - Call llm_service.chat() with messages and tools
    - _Requirements: 1.1, 1.2, 4.1, 4.2, 8.1, 8.7_
  
  - [ ] 6.2 Implement tool call handling in endpoint
    - Check if LLM response contains tool_calls
    - If yes, call llm_service.handle_tool_calls() to execute tools
    - Append assistant message with tool_calls to messages
    - Append tool results to messages
    - Call llm_service.chat() again for final answer
    - _Requirements: 8.3, 8.4, 8.5, 8.6_
  
  - [ ] 6.3 Update response format
    - Return final assistant message
    - Return updated conversation_history (all messages including tool calls)
    - Include metadata (llm_used, tokens_used, model, tool_calls_made)
    - Calculate processing_time
    - _Requirements: 5.1, 5.2, 5.4, 8.7, 8.9_
  
  - [ ] 6.4 Update health check endpoint
    - Add LLM status (enabled/disabled)
    - Include LLM usage statistics
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 7. Add logging and monitoring
  - [ ] 7.1 Add structured logging to LLMService
    - Log each LLM request with query preview
    - Log tokens used, model, response time
    - Log fallback usage with reason
    - Log errors with details for debugging
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ] 7.2 Add security logging
    - Ensure API key is never logged
    - Sanitize error messages before logging
    - _Requirements: 2.5_

- [ ] 8. Update frontend for conversation history management
  - [ ] 8.1 Update prototype/script.js to manage conversation history
    - Create conversationHistory array to store all messages
    - Initialize with empty array on page load
    - Update sendMessage() to include conversation_history in API request
    - _Requirements: 4.1, 4.2, 8.7_
  
  - [ ] 8.2 Update message handling to store history
    - When user sends message, add to conversationHistory as {role: "user", content: message}
    - When API responds, update conversationHistory with response.conversation_history
    - Display all messages from conversationHistory
    - _Requirements: 8.7, 8.8, 8.9_
  
  - [ ] 8.3 Add visual indicators for tool calls (optional)
    - Show when AI is searching for profiles (tool call in progress)
    - Display tool call information in chat (e.g., "Profil arıyorum...")
    - _Requirements: 8.6_
  
  - [ ] 8.4 Add conversation reset functionality
    - Add "Yeni Konuşma" button to clear conversationHistory
    - Clear chat display when reset
    - _Requirements: 8.8_

- [ ] 9. Create documentation
  - [ ] 9.1 Update README.md
    - Add Groq API setup instructions
    - Document environment variables
    - Add example .env configuration
    - Explain AI-driven architecture with function calling
    - Document conversation history management
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 8.1, 8.7_
  
  - [ ] 9.2 Add API documentation
    - Document conversation_history field in ChatRequest
    - Document updated ChatResponse with conversation_history
    - Document metadata field structure
    - Add example requests/responses with conversation history
    - Add example with tool calls
    - _Requirements: 4.1, 4.2, 5.1, 5.2, 5.4, 8.7, 8.9_

- [ ]* 10. Testing and validation
  - [ ]* 10.1 Write unit tests for GroqClient
    - Test request formatting with function calling
    - Test response parsing (both regular and tool call responses)
    - Test error handling (rate limit, timeout, API errors)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 8.10_
  
  - [ ]* 10.2 Write unit tests for LLMService
    - Test tool definitions generation
    - Test tool call execution
    - Test conversation history pass-through
    - Test fallback mechanism
    - Test API key validation
    - _Requirements: 1.5, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 8.1, 8.3, 8.4, 8.5_
  
  - [ ]* 10.3 Write integration tests
    - Test end-to-end chat flow with tool calling
    - Test multi-turn conversations with history
    - Test Turkish language responses
    - Test LLM deciding when to call tools vs answer from context
    - Test fallback scenarios
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 6.1, 6.2, 6.3, 8.1, 8.2, 8.6, 8.7, 8.8_
  
  - [ ]* 10.4 Manual testing
    - Test with real Groq API key
    - Verify Turkish responses quality
    - Test conversation memory (follow-up questions)
    - Test tool calling behavior (when LLM calls vs doesn't call)
    - Test rate limit behavior
    - Verify fallback works correctly
    - Test multi-turn conversation flow
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 6.1, 6.2, 6.3, 8.1, 8.2, 8.8_
