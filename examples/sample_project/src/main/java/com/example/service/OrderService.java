package com.example.service;

import com.example.model.Order;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class OrderService {

    private final Map<Long, Order> orderStore = new ConcurrentHashMap<>();
    private Long nextId = 1L;

    public Order createOrder(String userId, BigDecimal amount) {
        if (userId == null || userId.isBlank()) {
            throw new IllegalArgumentException("User ID must not be blank");
        }
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }

        Order order = new Order(userId, amount);
        order.setId(nextId++);
        orderStore.put(order.getId(), order);
        return order;
    }

    public List<Order> getOrdersByUser(String userId) {
        if (userId == null) {
            return List.of();
        }
        return orderStore.values().stream()
            .filter(o -> userId.equals(o.getUserId()))
            .toList();
    }

    public Order getOrderById(Long orderId) {
        return orderStore.get(orderId);
    }

    public boolean cancelOrder(Long orderId) {
        Order order = orderStore.get(orderId);
        if (order == null) {
            return false;
        }
        if (!"PENDING".equals(order.getStatus())) {
            throw new IllegalStateException("Only PENDING orders can be cancelled");
        }
        order.setStatus("CANCELLED");
        return true;
    }
}
