import requests
import json
import time
from datetime import datetime


BASE_URL = "http://localhost:8000"
#BASE_URL = "http://4.163.7.3,127:8000"


TEST_RESULTS = []


def log_test(name, passed, message="", response_data=None):
    """记录测试结果"""
    result = {
        "name": name,
        "passed": passed,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "response": response_data
    }
    TEST_RESULTS.append(result)
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{status}: {name}")
    if message:
        print(f"   消息: {message}")
    print()


def test_root_endpoint():
    """测试根路径是否正常返回"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        passed = response.status_code == 200
        data = response.json() if response.status_code == 200 else None
        log_test(
            "根路径测试",
            passed,
            f"状态码: {response.status_code}",
            data
        )
    except Exception as e:
        log_test("根路径测试", False, f"请求失败: {str(e)}")


def test_query_faq():
    """测试 FAQ 查询功能"""
    test_questions = [
        "什么是公司注册？",
        "如何申请营业执照？",
        "注册公司需要多长时间？"
    ]

    for question in test_questions:
        try:
            response = requests.post(
                f"{BASE_URL}/api/query",
                json={"question": question},
                timeout=30
            )
            passed = response.status_code == 200
            data = response.json() if response.status_code == 200 else None

            if passed and data:
                log_test(
                    f"FAQ查询测试: '{question}'",
                    True,
                    f"返回 {len(data)} 条结果",
                    data
                )
            else:
                log_test(
                    f"FAQ查询测试: '{question}'",
                    False,
                    f"状态码: {response.status_code}",
                    None
                )
        except Exception as e:
            log_test(f"FAQ查询测试: '{question}'", False, f"请求失败: {str(e)}")


def test_query_with_empty_question():
    """测试空问题是否被正确拒绝"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={"question": ""},
            timeout=10
        )
        passed = response.status_code == 400
        log_test(
            "空问题测试",
            passed,
            f"状态码: {response.status_code} (期望 400)",
            None
        )
    except Exception as e:
        log_test("空问题测试", False, f"请求失败: {str(e)}")


def test_update_index():
    """测试索引更新功能"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/update-index",
            timeout=60
        )
        passed = response.status_code == 200
        data = response.json() if response.status_code == 200 else None
        log_test(
            "索引更新测试",
            passed,
            f"状态码: {response.status_code}",
            data
        )
    except Exception as e:
        log_test("索引更新测试", False, f"请求失败: {str(e)}")


def save_results(filename="test_results.json"):
    """保存测试结果到文件"""
    summary = {
        "total": len(TEST_RESULTS),
        "passed": sum(1 for r in TEST_RESULTS if r["passed"]),
        "failed": sum(1 for r in TEST_RESULTS if not r["passed"]),
        "timestamp": datetime.now().isoformat(),
        "tests": TEST_RESULTS
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n测试结果已保存到: {filename}")
    print(f"总计: {summary['total']} 个测试")
    print(f"通过: {summary['passed']} 个")
    print(f"失败: {summary['failed']} 个")


def wait_for_service(max_wait=30):
    """等待服务启动"""
    print(f"等待服务启动 (最多 {max_wait} 秒)...")
    for i in range(max_wait):
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            if response.status_code == 200:
                print("服务已就绪！\n")
                return True
        except:
            pass
        time.sleep(1)
    print("服务未能在指定时间内启动")
    return False


def main():
    print("=" * 60)
    print("Milvus FAQ 检索系统 API 测试")
    print("=" * 60)
    print()

    if not wait_for_service():
        print("错误: 无法连接到服务。请确保服务正在运行 (uvicorn --app-dir . milvus_faq.main)")
        return

    print("-" * 60)
    print("开始测试...")
    print("-" * 60)
    print()

    test_root_endpoint()
    test_query_faq()
    test_query_with_empty_question()
    test_update_index()

    print("-" * 60)
    print("测试完成")
    print("-" * 60)

    save_results()


if __name__ == "__main__":
    main()
