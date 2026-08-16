# Implementation Plan: Screen Understanding Automation

## Overview

This implementation plan transforms Kypzer from coordinate-based automation to intelligent screen understanding. The system will enable natural language task execution, dynamic workflow generation, visual verification, error recovery, and pattern learning. Implementation uses Python and integrates with existing Kypzer components (screen_ai.py, memory.py, brain.py, actions.py).

## Tasks

- [ ] 1. Set up project structure and core data models
  - Create `screen_automation/` directory with `__init__.py`
  - Define data models using Pydantic: `ScreenContext`, `UIElement`, `Workflow`, `WorkflowStep`, `VerificationRule`, `RetryPolicy`, `WorkflowTemplate`, `ExecutionResult`, `ExecutionError`, `RecoveryAction`
  - Implement validation rules for all models (coordinates within bounds, confidence 0.0-1.0, timeout positive integer, etc.)
  - Create constants file for action types, error types, recovery strategies
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

- [ ]* 1.1 Write property tests for data model validation
  - **Property 1: Coordinate Boundary Safety** - All coordinates must be within screen bounds
  - **Property 2: Workflow Execution Completeness** - Execution results must reflect workflow completion status
  - **Validates: Requirements 9.1, 9.2, 9.3, 9.6, 9.7_

- [ ] 2. Implement Screen Context Manager component
  - [ ] 2.1 Create `ScreenContextManager` class with caching logic
    - Implement `get_current_context()` with 1-second cache TTL
    - Reuse `take_screenshot()` from screen_ai.py
    - Implement screen state hash computation for change detection
    - Add `get_active_application()` using pygetwindow
    - Implement cache invalidation on state changes
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [ ]* 2.2 Write property test for context caching
    - **Property 7: Context Caching Validity** - Cached context must be within TTL
    - **Validates: Requirements 2.2, 2.3_

  - [ ] 2.3 Implement screen element extraction methods
    - Add `get_visible_elements()` method
    - Implement `take_annotated_screenshot()` for debugging
    - Add `check_screen_state()` for verification
    - Implement `wait_for_state_change()` with timeout
    - _Requirements: 2.5, 2.6_

  - [ ]* 2.4 Write unit tests for Screen Context Manager
    - Test caching behavior and invalidation
    - Test screen state hash generation
    - Test active application detection
    - _Requirements: 2.1, 2.2, 2.3, 2.7_

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement Execution Engine component
  - [ ] 4.1 Create `ExecutionEngine` class with action primitives
    - Implement `execute_step()` for all action types (click, type, wait, verify, scroll, press_key)
    - Reuse `find_element_coordinates()` from screen_ai.py for click actions
    - Reuse `_native_click_at()` from actions.py for DPI-aware clicking
    - Implement type action using pyautogui
    - Implement wait action with configurable timeout
    - Implement scroll action
    - Implement press_key action using keyboard module
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ] 4.2 Add visual verification after actions
    - Implement `verify_step_success()` using Vision AI
    - Reuse `check_visual_condition()` from screen_ai.py
    - Handle verification timeout and failures
    - Capture diagnostic screenshots on verification failure
    - _Requirements: 4.5, 4.6_

  - [ ]* 4.3 Write property test for action execution
    - **Property 2: Coordinate Boundary Safety** - All click coordinates must be validated
    - **Validates: Requirements 4.3, 9.3_

  - [ ] 4.3 Implement execution state management
    - Add `get_execution_state()`, `pause_execution()`, `resume_execution()`, `abort_execution()`
    - Track completed steps and current step
    - Handle state transitions correctly
    - _Requirements: 4.7, 4.8, 4.9, 4.10, 4.11_

  - [ ] 4.4 Implement retry logic with exponential backoff
    - Create `execute_with_retry()` method
    - Implement exponential backoff: delay = 2^(attempt-1) seconds, max 10 seconds
    - Enforce max_retries limit from RetryPolicy
    - Log retry attempts and outcomes
    - _Requirements: 8.1, 8.2, 8.3, 8.7, 8.8_

  - [ ]* 4.5 Write property test for retry policy
    - **Property 3: Retry Policy Adherence** - Execution attempts must never exceed max_retries
    - **Validates: Requirements 8.1, 8.3, 8.7_

  - [ ]* 4.6 Write unit tests for Execution Engine
    - Test each action type execution
    - Test retry logic and backoff delays
    - Test execution state management
    - Test pause/resume/abort functionality
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 8.1, 8.2, 8.3_

- [ ] 5. Implement Adaptive Element Finding
  - [ ] 5.1 Create `find_element_with_adaptive_search()` function
    - Implement primary search using Vision AI
    - Generate semantic variations (button, icon, clickable)
    - Generate positional variations (at center, at top, at bottom)
    - Retry with variations up to 3 attempts
    - Validate coordinates are within screen bounds
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 5.2 Write property test for element finding
    - **Property 2: Coordinate Boundary Safety** - All returned coordinates must be within bounds
    - **Validates: Requirements 5.5, 5.6_

  - [ ]* 5.3 Write unit tests for adaptive element finding
    - Test semantic variations generation
    - Test positional variations generation
    - Test coordinate validation
    - Test retry behavior
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement Dynamic Workflow Generator component
  - [ ] 7.1 Create `DynamicWorkflowGenerator` class
    - Implement `generate_from_description()` using Gemini AI
    - Reuse Gemini model instance from brain.py
    - Build workflow generation prompt with task and screen context
    - Parse AI response into WorkflowStep objects
    - Add verification rules for state-changing actions
    - Configure retry policies for each step
    - Generate fallback steps for critical actions
    - Add final verification step
    - Compute workflow confidence score
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [ ] 7.2 Implement workflow refinement and confidence estimation
    - Add `refine_workflow()` method for iterative improvement
    - Implement `estimate_workflow_confidence()` calculation
    - _Requirements: 3.6_

  - [ ]* 7.3 Write unit tests for Dynamic Workflow Generator
    - Test workflow generation from task descriptions
    - Test verification rule inference
    - Test retry policy configuration
    - Test confidence score calculation
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ] 8. Implement Error Recovery Handler component
  - [ ] 8.1 Create `ErrorRecoveryHandler` class
    - Implement `handle_element_not_found()` with alternative descriptions
    - Implement `handle_state_verification_failed()` with state analysis
    - Implement `handle_timeout()` with diagnostic screenshot
    - Implement `suggest_alternative_action()` for failed steps
    - Implement `request_user_guidance()` for manual intervention
    - Track consecutive error count to prevent infinite loops
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11_

  - [ ]* 8.2 Write property test for error recovery
    - **Property 6: Error Recovery Termination** - Recovery must prevent infinite loops
    - **Validates: Requirements 6.8_

  - [ ]* 8.3 Write unit tests for Error Recovery Handler
    - Test each error type recovery strategy
    - Test alternative action generation
    - Test user guidance request formatting
    - Test consecutive error tracking
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11_

- [ ] 9. Implement Workflow Engine component
  - [ ] 9.1 Create `WorkflowEngine` class
    - Implement `generate_workflow()` that delegates to DynamicWorkflowGenerator
    - Implement `execute_workflow()` that orchestrates ExecutionEngine
    - Integrate error recovery in workflow execution loop
    - Handle execution results and error collection
    - _Requirements: 1.3, 1.4, 4.4_

  - [ ] 9.2 Implement workflow execution with recovery
    - Create `execute_workflow_with_recovery()` method
    - Implement main execution loop with step iteration
    - Apply retry policy for failed steps
    - Execute verification after each step
    - Handle fallback steps insertion
    - Invoke error recovery on failures
    - Support pause/resume/abort controls
    - Capture final screen state
    - _Requirements: 4.4, 4.5, 4.6, 4.7, 4.8, 6.1, 6.2, 6.3, 6.11_

  - [ ]* 9.3 Write property test for workflow execution
    - **Property 1: Workflow Execution Completeness** - Result must reflect completion status
    - **Property 8: Workflow Step Ordering Preservation** - Steps must execute in order
    - **Validates: Requirements 1.5, 1.6_

  - [ ] 9.3 Implement template management
    - Add `load_template()` method
    - Add `save_template()` method
    - Implement `adapt_workflow()` for error-based adaptation
    - _Requirements: 7.1, 7.2_

  - [ ]* 9.4 Write unit tests for Workflow Engine
    - Test workflow generation delegation
    - Test workflow execution orchestration
    - Test error recovery integration
    - Test template load/save
    - _Requirements: 1.3, 1.4, 1.5, 1.6_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement Pattern Learning System component
  - [ ] 11.1 Create `PatternLearningSystem` class
    - Implement `record_successful_workflow()` with ChromaDB storage
    - Reuse ChromaDB client from memory.py
    - Create "automation_workflows" collection with embeddings
    - Store workflow with metadata (timestamp, application, screen state, confidence)
    - _Requirements: 7.1, 7.2_

  - [ ] 11.2 Implement pattern matching and template creation
    - Implement `find_similar_patterns()` using semantic similarity search
    - Filter by confidence score threshold (>0.7)
    - Add `create_template_from_workflow()` after 3 successes
    - Implement `update_template_confidence()` based on success/failure
    - Mark templates unreliable when confidence drops below 0.3
    - Filter templates by application context
    - _Requirements: 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_

  - [ ] 11.3 Implement template retrieval
    - Add `get_most_reliable_template()` method
    - Ensure query returns within 1 second
    - _Requirements: 7.10_

  - [ ]* 11.4 Write property test for pattern learning
    - **Property 5: Template Confidence Monotonicity** - Confidence updates must reflect usage
    - **Property 9: Memory Recording Completeness** - Successful workflows must be recorded
    - **Validates: Requirements 7.5, 7.6, 1.5_

  - [ ]* 11.5 Write unit tests for Pattern Learning System
    - Test workflow storage in ChromaDB
    - Test semantic similarity search
    - Test template creation logic
    - Test confidence score updates
    - Test template filtering by context
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10_

- [ ] 12. Implement main task execution orchestration
  - [ ] 12.1 Create `execute_natural_language_task()` function
    - Implement main algorithm from design document
    - Search for similar patterns using PatternLearningSystem
    - Use template if found, else generate new workflow
    - Execute workflow using WorkflowEngine
    - Record successful workflows for learning
    - Update template confidence based on result
    - Create new template for repeated tasks
    - Return ExecutionResult with duration and status
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [ ]* 12.2 Write property test for task execution
    - **Property 10: Visual Verification Timeout Guarantee** - Verification must timeout correctly
    - **Validates: Requirements 4.5_

  - [ ]* 12.3 Write integration tests for end-to-end task execution
    - Test simple task execution (1-3 steps)
    - Test complex task execution (5-10 steps)
    - Test template reuse scenario
    - Test error recovery scenario
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [ ] 13. Integrate with existing Kypzer main.py controller
  - [ ] 13.1 Add fast route for screen automation
    - Create `_fast_screen_automation_route()` function
    - Match automation keywords: "fill out", "complete", "automate", "click on", "find and click"
    - Return action dict with SCREEN_AUTOMATE_TASK action
    - Insert fast route before offline intent matching
    - Prevent new commands during active automation
    - _Requirements: 11.1, 11.2, 11.6_

  - [ ] 13.2 Add TTS response handling
    - Speak confirmation on success
    - Speak error message on failure
    - _Requirements: 11.4, 11.5_

  - [ ] 13.3 Handle graceful fallback
    - Check if screen automation components are installed
    - Fall back to Gemini AI if not available
    - _Requirements: 11.7_

  - [ ]* 13.4 Write integration tests for main.py integration
    - Test fast route matching
    - Test command routing to screen automation
    - Test fallback behavior
    - _Requirements: 11.1, 11.2, 11.3, 11.7_

- [ ] 14. Integrate with existing Kypzer actions.py
  - [ ] 14.1 Add SCREEN_AUTOMATE_TASK action handler
    - Import `execute_natural_language_task` and `ScreenContextManager`
    - Handle SCREEN_AUTOMATE_TASK action in `execute_action()`
    - Get current screen context
    - Execute natural language task
    - Print success/failure status
    - _Requirements: 12.6_

  - [ ] 14.2 Reuse existing action primitives
    - Confirm `_native_click_at()` is used for clicks (already implemented)
    - Confirm DPI-aware coordinate calculations work correctly
    - _Requirements: 12.7_

  - [ ]* 14.3 Write unit tests for action handler
    - Test SCREEN_AUTOMATE_TASK execution
    - Test error handling
    - _Requirements: 12.6_

- [ ] 15. Integrate with existing Kypzer brain.py
  - [ ] 15.1 Update system prompt with screen automation actions
    - Add SCREEN_AUTOMATE_TASK to action documentation
    - Provide examples of usage
    - Recommend SCREEN_AUTOMATE_TASK over individual SCREEN_CLICK_ELEMENT for complex interactions
    - _Requirements: 12.5_

  - [ ] 15.2 Ensure Gemini model instance is accessible
    - Confirm brain.py exports Gemini model for workflow generation
    - _Requirements: 12.5_

- [ ] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 17. Implement configuration and customization support
  - [ ] 17.1 Create configuration file and loader
    - Create `screen_automation/config.py` with default settings
    - Support custom retry limits, timeouts, cache TTL, JPEG quality, confidence threshold
    - Load configuration from env.env or config file
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

  - [ ] 17.2 Add application-specific template prioritization
    - Filter templates by application context
    - _Requirements: 16.6_

  - [ ] 17.3 Add verbose logging support
    - Implement detailed execution trace logging
    - Log timing and intermediate results
    - _Requirements: 16.8_

  - [ ]* 17.4 Write unit tests for configuration
    - Test configuration loading
    - Test default values
    - Test custom value override
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [ ] 18. Implement workflow persistence and recovery
  - [ ] 18.1 Add workflow state persistence
    - Record workflow_id and start timestamp on execution start
    - Record step completion status and timestamps
    - Save execution state on interruption
    - Store final ExecutionResult with duration and errors
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [ ] 18.2 Implement workflow resume capability
    - Add workflow history query function
    - Implement resume from saved state
    - Detect screen state changes that prevent resume
    - Offer restart option when resume impossible
    - _Requirements: 13.5, 13.6, 13.7_

  - [ ]* 18.3 Write unit tests for workflow persistence
    - Test state saving on interruption
    - Test workflow resume from saved state
    - Test history querying
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

- [ ] 19. Implement security and privacy features
  - [ ] 19.1 Add input validation and safety checks
    - Validate API keys are read from env.env only
    - Never log or expose API keys
    - Sanitize workflow data to remove sensitive information
    - Whitelist allowed action types
    - Require confirmation for dangerous actions
    - Implement rate limiting (10 workflows per minute)
    - _Requirements: 14.1, 14.5, 14.7, 14.8_

  - [ ] 19.2 Implement screenshot privacy protection
    - Avoid storing screenshots with sensitive field labels
    - Require user opt-in for screenshot retention
    - Securely delete cached screenshots
    - _Requirements: 14.2, 14.3, 14.4_

  - [ ] 19.3 Ensure secure API communication
    - Confirm HTTPS is used for all API calls (Groq, Gemini)
    - Log API errors without exposing credentials
    - _Requirements: 14.9, 14.10_

  - [ ]* 19.4 Write security tests
    - Test API key protection
    - Test input sanitization
    - Test action type whitelisting
    - Test rate limiting
    - _Requirements: 14.1, 14.5, 14.7, 14.8_

- [ ] 20. Implement error reporting and diagnostics
  - [ ] 20.1 Enhance error recording
    - Record error type, message, and step_id for all failures
    - Capture diagnostic screenshots on element finding failures
    - Record expected vs actual state for verification failures
    - Log API response codes and error details
    - Store error screenshots temporarily for review
    - Record all errors chronologically in ExecutionResult
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.6, 15.7, 15.8_

  - [ ] 20.2 Add human-readable error explanations
    - Provide clear error explanations and suggested solutions
    - _Requirements: 15.9_

  - [ ] 20.3 Track recovery actions in logs
    - Log recovery strategy and outcome
    - _Requirements: 15.5_

  - [ ]* 20.4 Write unit tests for error reporting
    - Test error recording for each error type
    - Test diagnostic screenshot capture
    - Test error explanation generation
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.9_

- [ ] 21. Implement monitoring and observability
  - [ ] 21.1 Add execution metrics tracking
    - Record execution duration, success rate, retry count, error types
    - Track template success_count and failure_count
    - Track API response times and error rates
    - Track screenshot cache hit rate and size
    - Track error recovery success rate by error type
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

  - [ ] 21.2 Implement metrics query interface
    - Add function to query aggregated statistics for time period
    - Log performance warnings when thresholds are breached
    - _Requirements: 18.6, 18.7_

  - [ ]* 21.3 Write unit tests for monitoring
    - Test metrics recording
    - Test metrics aggregation
    - Test performance warning triggers
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7_

- [ ] 22. Implement user guidance and fallback mechanisms
  - [ ] 22.1 Add user guidance request handling
    - Display current screenshot when requesting guidance
    - Provide clear instructions for what action is needed
    - Accept user input (click location or cancel)
    - Resume workflow with user-provided coordinates
    - Abort workflow on user cancel
    - _Requirements: 19.1, 19.2, 19.3, 19.4_

  - [ ] 22.2 Record manual interventions for learning
    - Log manual actions as learning opportunities
    - _Requirements: 19.6_

  - [ ] 22.3 Implement coordinate-based fallback
    - Offer coordinate-based fallback templates when available
    - _Requirements: 19.7_

  - [ ]* 22.4 Write unit tests for user guidance
    - Test guidance request formatting
    - Test user input handling
    - Test workflow resume after guidance
    - Test workflow abort on cancel
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_

- [ ] 23. Implement workflow composition and reusability
  - [ ] 23.1 Add sub-workflow support
    - Expand sub-workflow references inline during execution
    - Substitute template steps with appropriate context
    - Apply error recovery at sub-workflow level
    - Validate total step count does not exceed 50 steps
    - _Requirements: 20.1, 20.2, 20.3, 20.4_

  - [ ] 23.2 Implement template extraction from common patterns
    - Identify common step sequences across workflows
    - Create reusable templates automatically
    - Suggest template extraction to user
    - _Requirements: 20.5, 20.6_

  - [ ]* 23.3 Write unit tests for workflow composition
    - Test sub-workflow expansion
    - Test template substitution
    - Test step count validation
    - Test template extraction
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6_

- [ ] 24. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 25. Create comprehensive documentation
  - [ ] 25.1 Write API documentation
    - Document all public classes and methods
    - Include docstrings with preconditions, postconditions, examples
    - Document data models with field descriptions

  - [ ] 25.2 Create user guide
    - Explain how to use natural language commands
    - Provide examples of supported task types
    - Document configuration options
    - Explain error messages and recovery strategies

  - [ ] 25.3 Write integration guide
    - Document integration with main.py, actions.py, brain.py
    - Explain how to extend with custom actions
    - Document template creation and management

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements from requirements.md for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- All code will be written in **Python** as selected by the user
- Implementation reuses existing Kypzer components for consistency and efficiency
