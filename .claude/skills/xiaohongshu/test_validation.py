#!/usr/bin/env python3
"""
小红书 Skill 冒烟测试脚本
测试参数验证逻辑
"""

def test_title_validation():
    """测试标题验证"""
    print("=" * 50)
    print("测试 1: 标题验证")
    print("=" * 50)

    test_cases = [
        ("我的日常穿搭", True, "正常标题"),
        ("三亚5日游攻略｜超详细", True, "使用特殊字符"),
        ("这是一个超级超级超级超级超级长的标题啊啊啊", False, "超过20字符（21字符）"),
        ("", False, "空标题"),
        ("a" * 20, True, "正好20字符"),
        ("a" * 21, False, "21字符"),
    ]

    passed = 0
    failed = 0

    for title, expected_valid, description in test_cases:
        is_valid = len(title) <= 20 and len(title) > 0
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"

        if is_valid == expected_valid:
            passed += 1
        else:
            failed += 1

        print(f"{status} - {description}")
        print(f"   标题: '{title}' (长度: {len(title)})")
        print(f"   预期: {'有效' if expected_valid else '无效'}, 实际: {'有效' if is_valid else '无效'}")
        print()

    print(f"总计: {passed} 通过, {failed} 失败\n")
    return failed == 0


def test_content_validation():
    """测试内容验证"""
    print("=" * 50)
    print("测试 2: 内容验证")
    print("=" * 50)

    test_cases = [
        ("今天分享一套简约风穿搭", True, "正常内容"),
        ("a" * 1000, True, "正好1000字符"),
        ("a" * 1001, False, "1001字符"),
        ("", False, "空内容"),
        ("这是一篇很长的内容..." + "很长" * 500, False, "超长内容"),
    ]

    passed = 0
    failed = 0

    for content, expected_valid, description in test_cases:
        is_valid = len(content) <= 1000 and len(content) > 0
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"

        if is_valid == expected_valid:
            passed += 1
        else:
            failed += 1

        content_preview = content[:50] + "..." if len(content) > 50 else content
        print(f"{status} - {description}")
        print(f"   内容: '{content_preview}' (长度: {len(content)})")
        print(f"   预期: {'有效' if expected_valid else '无效'}, 实际: {'有效' if is_valid else '无效'}")
        print()

    print(f"总计: {passed} 通过, {failed} 失败\n")
    return failed == 0


def test_image_path_validation():
    """测试图片路径验证"""
    print("=" * 50)
    print("测试 3: 图片路径验证")
    print("=" * 50)

    test_cases = [
        ("/Users/liuyishou/Pictures/photo.jpg", True, "绝对路径"),
        ("https://example.com/image.jpg", True, "HTTP URL"),
        ("http://example.com/image.jpg", True, "HTTP URL"),
        ("~/Pictures/photo.jpg", False, "使用波浪号"),
        ("photo.jpg", False, "相对路径"),
        ("./images/photo.jpg", False, "相对路径（当前目录）"),
        ("/absolute/path/image.png", True, "Linux绝对路径"),
    ]

    passed = 0
    failed = 0

    for path, expected_valid, description in test_cases:
        # 简化验证：检查是否是绝对路径或 URL
        is_valid = path.startswith('http://') or path.startswith('https://') or path.startswith('/')
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"

        if is_valid == expected_valid:
            passed += 1
        else:
            failed += 1

        print(f"{status} - {description}")
        print(f"   路径: '{path}'")
        print(f"   预期: {'有效' if expected_valid else '无效'}, 实际: {'有效' if is_valid else '无效'}")
        print()

    print(f"总计: {passed} 通过, {failed} 失败\n")
    return failed == 0


def test_video_path_validation():
    """测试视频路径验证"""
    print("=" * 50)
    print("测试 4: 视频路径验证")
    print("=" * 50)

    test_cases = [
        ("/Users/liuyishou/Videos/travel.mp4", True, "绝对路径"),
        ("https://example.com/video.mp4", False, "URL（不支持）"),
        ("~/Videos/travel.mp4", False, "使用波浪号"),
        ("video.mp4", False, "相对路径"),
        ("/absolute/path/video.mov", True, "绝对路径（MOV格式）"),
    ]

    passed = 0
    failed = 0

    for path, expected_valid, description in test_cases:
        # 视频必须是绝对路径（不支持 URL）
        is_valid = path.startswith('/') and not path.startswith('http')
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"

        if is_valid == expected_valid:
            passed += 1
        else:
            failed += 1

        print(f"{status} - {description}")
        print(f"   路径: '{path}'")
        print(f"   预期: {'有效' if expected_valid else '无效'}, 实际: {'有效' if is_valid else '无效'}")
        print()

    print(f"总计: {passed} 通过, {failed} 失败\n")
    return failed == 0


def test_complete_post_validation():
    """测试完整发布数据验证"""
    print("=" * 50)
    print("测试 5: 完整发布数据验证")
    print("=" * 50)

    test_cases = [
        {
            "name": "正常图文发布",
            "data": {
                "title": "我的日常穿搭",
                "content": "今天分享一套简约风穿搭",
                "images": ["/Users/test/image.jpg"]
            },
            "expected_valid": True
        },
        {
            "name": "标题过长",
            "data": {
                "title": "这是一个超级超级超级超级超级长的标题啊啊啊",
                "content": "内容",
                "images": ["/Users/test/image.jpg"]
            },
            "expected_valid": False
        },
        {
            "name": "内容过长",
            "data": {
                "title": "标题",
                "content": "a" * 1001,
                "images": ["/Users/test/image.jpg"]
            },
            "expected_valid": False
        },
        {
            "name": "图片路径无效",
            "data": {
                "title": "标题",
                "content": "内容",
                "images": ["~/image.jpg"]
            },
            "expected_valid": False
        },
        {
            "name": "多图发布",
            "data": {
                "title": "多图测试",
                "content": "多图内容",
                "images": ["/path/1.jpg", "/path/2.jpg", "/path/3.jpg"]
            },
            "expected_valid": True
        },
    ]

    passed = 0
    failed = 0

    for test_case in test_cases:
        data = test_case["data"]
        expected_valid = test_case["expected_valid"]

        # 验证逻辑
        title_valid = 0 < len(data["title"]) <= 20
        content_valid = 0 < len(data["content"]) <= 1000
        images_valid = all(
            img.startswith('http://') or img.startswith('https://') or img.startswith('/')
            for img in data["images"]
        )

        is_valid = title_valid and content_valid and images_valid
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"

        if is_valid == expected_valid:
            passed += 1
        else:
            failed += 1

        print(f"{status} - {test_case['name']}")
        print(f"   标题: '{data['title']}' (长度: {len(data['title'])}) - {'✓' if title_valid else '✗'}")
        print(f"   内容长度: {len(data['content'])} - {'✓' if content_valid else '✗'}")
        print(f"   图片数量: {len(data['images'])} - {'✓' if images_valid else '✗'}")
        print(f"   预期: {'有效' if expected_valid else '无效'}, 实际: {'有效' if is_valid else '无效'}")
        print()

    print(f"总计: {passed} 通过, {failed} 失败\n")
    return failed == 0


def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("小红书 Skill 冒烟测试")
    print("=" * 50 + "\n")

    all_passed = True

    all_passed &= test_title_validation()
    all_passed &= test_content_validation()
    all_passed &= test_image_path_validation()
    all_passed &= test_video_path_validation()
    all_passed &= test_complete_post_validation()

    print("=" * 50)
    if all_passed:
        print("🎉 所有测试通过！")
        print("=" * 50)
        return 0
    else:
        print("❌ 部分测试失败")
        print("=" * 50)
        return 1


if __name__ == "__main__":
    exit(main())
