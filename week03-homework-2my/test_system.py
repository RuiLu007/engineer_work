#!/usr/bin/env python3
# 测试脚本 - 测试优化后的系统功能

import requests
import time
import json

# 测试配置
BASE_URL = "http://localhost:8000"

# 测试 Milvus FAQ 系统
def test_milvus_faq():
    print("========================================")
    print("测试 Milvus FAQ 系统")
    print("========================================")
    
    # 测试健康检查
    print("1. 测试健康检查接口...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    
    # 测试查询接口
    print("\n2. 测试查询接口...")
    test_questions = ["如何退货？", "如何查询订单？", "如何联系客服？"]
    
    for question in test_questions:
        payload = {"question": question}
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/query", json=payload)
        end_time = time.time()
        
        print(f"   问题: {question}")
        print(f"   状态码: {response.status_code}")
        print(f"   响应时间: {end_time - start_time:.4f}秒")
        if response.status_code == 200:
            results = response.json()
            print(f"   结果数量: {len(results)}")
            if results:
                print(f"   最相关结果: {results[0]['question']}")
                print(f"   答案: {results[0]['answer']}")
                print(f"   分数: {results[0]['score']}")
                print(f"   置信度: {results[0]['confidence']}")
    
    # 测试热更新索引
    print("\n3. 测试热更新索引接口...")
    response = requests.post(f"{BASE_URL}/api/update-index")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")

# 测试 GraphRAG 系统
def test_graph_rag():
    print("\n========================================")
    print("测试 GraphRAG 系统")
    print("========================================")
    
    # 测试健康检查
    print("1. 测试健康检查接口...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    
    # 测试查询接口
    print("\n2. 测试查询接口...")
    test_questions = ["星辰科技的最大股东是谁？", "未来集团的股东有哪些？"]
    
    for question in test_questions:
        payload = {"question": question}
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/query", json=payload)
        end_time = time.time()
        
        print(f"   问题: {question}")
        print(f"   状态码: {response.status_code}")
        print(f"   响应时间: {end_time - start_time:.4f}秒")
        if response.status_code == 200:
            result = response.json()
            print(f"   最终答案: {result['final_answer']}")
            print(f"   识别的实体: {result['entity_name']}")
            print(f"   推理路径: {len(result['reasoning_path'])} 步")
    
    # 测试重新初始化引擎
    print("\n3. 测试重新初始化引擎接口...")
    response = requests.post(f"{BASE_URL}/api/reinitialize")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")

if __name__ == "__main__":
    print("开始测试优化后的系统功能...")
    print("注意：请确保系统已经启动并运行在 http://localhost:8000")
    print("\n请选择要测试的系统:")
    print("1. Milvus FAQ 系统")
    print("2. GraphRAG 系统")
    choice = input("请输入选项 (1-2): ")
    
    if choice == "1":
        test_milvus_faq()
    elif choice == "2":
        test_graph_rag()
    else:
        print("无效选项")
    
    print("\n测试完成！")