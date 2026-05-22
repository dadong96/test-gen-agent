# Order Service PRD

## 1. Overview
The Order Service handles order creation, retrieval, and status management for the e-commerce platform.

## 2. Business Rules

### 2.1 Order Creation
- BR-001: Order amount must be greater than zero
- BR-002: User ID is required and must not be blank
- BR-003: Orders are created in PENDING status by default
- BR-004: Duplicate orders (same user + same amount within 1 minute) should be rejected

### 2.2 Order Retrieval
- BR-005: Users can only retrieve their own orders
- BR-006: Empty result set returns an empty list, not an error

## 3. Non-Functional Requirements
- Order creation must be idempotent
- System should handle concurrent order creation gracefully
