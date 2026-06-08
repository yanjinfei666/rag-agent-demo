"""
Day 3：字符串、文件读写、异常处理
实战：读取文件并统计词频Top10
"""

import os
import re
from collections import Counter

# ============ 1. 字符串操作 ============
print("=" * 20, "字符串操作", "=" * 20)

text = "  Hello, Python World!  "
print(f"原始: '{text}'")
print(f"去空格: '{text.strip()}'")
print(f"小写: '{text.lower()}'")
print(f"替换: '{text.replace('World', '大模型')}'")

# split 和 join
sentence = "苹果,香蕉,橘子,葡萄"
fruits_list = sentence.split("，")
print(f"split结果: {fruits_list}")
print(f"join结果: {' | '.join(fruits_list)}")

# 切片
long_text = "Python大模型应用开发"
print(f"前6个字符: '{long_text[:6]}'")
print(f"后2个字符: '{long_text[-2:]}'")
print(f"每隔2个取: '{long_text[::2]}'")


# ============ 2. 文件读写 ============
print("\n" + "=" * 20, "文件读写", "=" * 20)

# 写文件
with open("data/test_write.txt", "w", encoding="utf-8") as f:
    f.write("第一行：大模型应用开发\n")
    f.write("第二行：RAG技术实战\n")
    f.write("第三行：大模型改变世界\n")

# 读文件（全部）
with open("data/test_write.txt", "r", encoding="utf-8") as f:
    content = f.read()
    print("全部内容:")
    print(content)

# 读文件（逐行）
print("逐行读取:")
with open("data/test_write.txt", "r", encoding="utf-8") as f:
    for line_no, line in enumerate(f, 1):
        print(f"  第{line_no}行: {line.strip()}")


# ============ 3. 异常处理 ============
print("\n" + "=" * 20, "异常处理", "=" * 20)

def safe_read_file(file_path):
    """安全地读取文件，处理各种异常"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        return None
    except PermissionError:
        print(f"❌ 没有权限读取: {file_path}")
        return None
    except UnicodeDecodeError:
        print(f"❌ 文件编码错误，尝试用gbk编码...")
        try:
            with open(file_path, "r", encoding="gbk") as f:
                return f.read()
        except Exception as e:
            print(f"❌ 仍然失败: {e}")
            return None
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return None

# 测试异常处理
print("测试不存在的文件:")
safe_read_file("data/不存在.txt")
print("\n测试正常文件:")
result = safe_read_file("data/test_write.txt")
print(result)


# ============ 4. 实战：词频统计 ============
print("=" * 20, "词频统计实战", "=" * 20)

def word_frequency_analysis(file_path, top_n=10):
    """
    读取文本文件，统计词频Top N
    处理逻辑：
    1. 读取文件
    2. 用正则提取中文字符
    3. 统计词频
    4. 返回Top N
    """
    # 读取文件
    content = safe_read_file(file_path)
    if content is None:
        return []
    
    # 清洗文本：去除标点、数字、英文字母，只保留中文
    cleaned = re.sub(r'[^\u4e00-\u9fff]', '', content)
    
    # 如果没有中文，尝试按英文单词统计
    if not cleaned:
        words = re.findall(r'\b\w+\b', content.lower())
    else:
        # 中文按单字统计
        words = list(cleaned)
    
    # 统计词频
    word_count = Counter(words)
    
    # 返回Top N
    return word_count.most_common(top_n)


# 测试词频统计（如果sample.txt不存在，先自动创建一个）
sample_path = "data/sample.txt"
if not os.path.exists(sample_path):
    os.makedirs("data", exist_ok=True)
    sample_text = """
    大模型技术的发展正在深刻改变软件工程的面貌。从代码生成到智能问答，
    大模型展现出了强大的能力。然而，如何将大模型与企业的私有数据结合，
    是一个关键的挑战。RAG技术通过检索增强生成的方式，为大模型提供了
    访问外部知识库的能力。在大模型应用开发中，我们需要注意提示工程、
    向量检索、文档解析等核心技术。掌握大模型应用开发，是未来软件工程师
    的重要技能。大模型的潜力还远未被完全挖掘，我们需要不断探索和创新。
    """ * 20  # 重复20次让文件变大
    with open(sample_path, "w", encoding="utf-8") as f:
        f.write(sample_text)
    print(f"✓ 已自动创建示例文件: {sample_path}")

# 执行词频统计
top_words = word_frequency_analysis(sample_path, top_n=10)

print(f"\n文件: {sample_path}")
print(f"词频Top {len(top_words)}:")
print("-" * 30)
for i, (word, count) in enumerate(top_words, 1):
    bar = "█" * (count // 10)
    print(f"{i:2}. '{word}' 出现 {count:3} 次 {bar}")

# 额外：统计文件大小
file_size = os.path.getsize(sample_path)
print(f"\n文件大小: {file_size:,} 字节 ({file_size/1024:.1f} KB)")

print("\n🎉 Day 3 完成！")
