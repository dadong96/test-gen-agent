"""Tests for Java AST parser using tree-sitter."""

from pathlib import Path

import pytest

from src.core.ast_parser import JavaClassInfo, parse_java_file, parse_java_source


SAMPLE_JAVA = """
package com.example.service;

import java.util.List;
import java.math.BigDecimal;

public class OrderService {

    private final OrderRepository repo;

    public OrderService(OrderRepository repo) {
        this.repo = repo;
    }

    public Order createOrder(String userId, BigDecimal amount) {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
        Order order = new Order(userId, amount);
        return repo.save(order);
    }

    public List<Order> getOrdersByUser(String userId) {
        return repo.findByUserId(userId);
    }

    private void validateOrder(Order order) {
        if (order == null) {
            throw new NullPointerException("Order cannot be null");
        }
    }
}
"""


def test_parse_class_name():
    info = parse_java_source(SAMPLE_JAVA)
    assert info.class_name == "OrderService"
    assert info.package == "com.example.service"


def test_parse_methods():
    info = parse_java_source(SAMPLE_JAVA)
    methods = {m.name: m for m in info.methods}
    assert "createOrder" in methods
    assert "getOrdersByUser" in methods
    assert "validateOrder" in methods


def test_parse_method_params():
    info = parse_java_source(SAMPLE_JAVA)
    methods = {m.name: m for m in info.methods}
    create = methods["createOrder"]
    assert len(create.parameters) == 2
    assert create.parameters[0] == ("userId", "String")
    assert create.parameters[1] == ("amount", "BigDecimal")


def test_parse_return_type():
    info = parse_java_source(SAMPLE_JAVA)
    methods = {m.name: m for m in info.methods}
    assert methods["createOrder"].return_type == "Order"
    assert methods["getOrdersByUser"].return_type == "List<Order>"


def test_parse_imports():
    info = parse_java_source(SAMPLE_JAVA)
    assert "java.util.List" in info.imports
    assert "java.math.BigDecimal" in info.imports


def test_public_methods_only_filter():
    info = parse_java_source(SAMPLE_JAVA)
    public_methods = [m for m in info.methods if m.is_public]
    names = [m.name for m in public_methods]
    assert "createOrder" in names
    assert "getOrdersByUser" in names
    assert "validateOrder" not in names


def test_parse_empty_class():
    source = "public class Empty {}"
    info = parse_java_source(source)
    assert info.class_name == "Empty"
    assert info.methods == []
