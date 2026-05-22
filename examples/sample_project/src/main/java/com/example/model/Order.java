package com.example.model;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public class Order {
    private Long id;
    private String userId;
    private BigDecimal amount;
    private String status;
    private LocalDateTime createdAt;

    public Order() {}

    public Order(String userId, BigDecimal amount) {
        this.userId = userId;
        this.amount = amount;
        this.status = "PENDING";
        this.createdAt = LocalDateTime.now();
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getUserId() { return userId; }
    public BigDecimal getAmount() { return amount; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public LocalDateTime getCreatedAt() { return createdAt; }
}
