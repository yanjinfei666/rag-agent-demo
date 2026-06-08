"""
Day 4：面向对象（class、self、__init__）、模块导入
实战：将Day 3的词频统计重构为面向对象类
"""

import os
import re
from collections import Counter
from datetime import datetime


# ============ 1. 基础类定义 ============
print("=" * 20, "基础面向对象", "=" * 20)

class Student:
    """学生类"""
    
    # 类属性（所有实例共享）
    school = "XX大学"
    
    def __init__(self, name, age, grade):
        """构造函数：初始化实例属性"""
        self.name = name
        self.age = age
        self.grade = grade
        self.create_time = datetime.now()
    
    def introduce(self):
        """实例方法"""
        return f"我叫{self.name}，今年{self.age}岁，{self.grade}年级"
    
    def is_adult(self):
        """判断是否成年"""
        return self.age >= 18
    
    @classmethod
    def change_school(cls, new_school):
        """类方法：修改类属性"""
        cls.school = new_school
    
    @staticmethod
    def is_valid_age(age):
        """静态方法：不依赖类和实例"""
        return 0 < age < 150


# 创建对象
s1 = Student("张三", 20, "大三")
s2 = Student("李四", 17, "大一")

print(s1.introduce())
print(f"{s1.name} 成年了吗？{s1.is_adult()}")
print(f"{s2.name} 成年了吗？{s2.is_adult()}")
print(f"学校: {Student.school}")

# 测试静态方法
print(f"年龄150有效吗？{Student.is_valid_age(150)}")


# ============ 2. 继承 ============
print("\n" + "=" * 20, "继承", "=" * 20)

class CSStudent(Student):
    """计算机专业学生，继承自Student"""
    
    def __init__(self, name, age, grade, programming_lang):
        super().__init__(name, age, grade)  # 调用父类构造
        self.programming_lang = programming_lang
    
    def introduce(self):
        """重写父类方法"""
        base = super().introduce()
        return f"{base}，擅长{self.programming_lang}"
    
    def code(self):
        return f"{self.name}正在用{self.programming_lang}写代码..."


cs_student = CSStudent("王五", 21, "大三", "Python")
print(cs_student.introduce())
print(cs_student.code())


# ============ 3. 模块化：将词频统计封装成类 ============
print("\n" + "=" * 20, "词频分析器（面向对象版）", "=" * 20)

class WordFrequencyAnalyzer:
    """词频分析器"""
    
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.raw_content = None
        self.cleaned_content = None
        self.word_counter = None
    
    def load_file(self, file_path=None):
        """读取文件"""
        path = file_path or self.file_path
        if not path:
            raise ValueError("请提供文件路径")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.raw_content = f.read()
                print(f"✓ 成功读取文件: {path}")
                print(f"  文件大小: {len(self.raw_content):,} 字符")
                return self
        except FileNotFoundError:
            raise FileNotFoundError(f"文件不存在: {path}")
        except Exception as e:
            raise Exception(f"读取文件失败: {e}")
    
    def clean_text(self, mode="chinese"):
        """清洗文本"""
        if self.raw_content is None:
            raise ValueError("请先调用 load_file() 读取文件")
        
        if mode == "chinese":
            # 只保留中文字符
            self.cleaned_content = re.sub(r'[^\u4e00-\u9fff]', '', self.raw_content)
            self.words = list(self.cleaned_content)
        elif mode == "english":
            # 提取英文单词
            self.words = re.findall(r'\b[a-zA-Z]+\b', self.raw_content.lower())
        else:
            # 混合模式
            chinese_chars = re.sub(r'[^\u4e00-\u9fff]', '', self.raw_content)
            english_words = re.findall(r'\b[a-zA-Z]+\b', self.raw_content.lower())
            self.words = list(chinese_chars) + english_words
        
        print(f"✓ 清洗完成，共提取 {len(self.words):,} 个词/字")
        return self
    
    def count(self):
        """统计词频"""
        if not self.words:
            raise ValueError("请先调用 clean_text() 清洗文本")
        
        self.word_counter = Counter(self.words)
        return self
    
    def get_top(self, n=10):
        """获取Top N"""
        if self.word_counter is None:
            raise ValueError("请先调用 count() 统计词频")
        
        return self.word_counter.most_common(n)
    
    def get_total_unique(self):
        """获取不重复词的总数"""
        if self.word_counter is None:
            raise ValueError("请先调用 count() 统计词频")
        return len(self.word_counter)
    
    def print_report(self, top_n=10):
        """打印完整报告"""
        if self.word_counter is None:
            raise ValueError("请先完成分析")
        
        top_words = self.get_top(top_n)
        
        print("\n" + "=" * 50)
        print(f"  词频分析报告")
        print("=" * 50)
        print(f"  文件路径: {self.file_path}")
        print(f"  原始字符数: {len(self.raw_content):,}")
        print(f"  提取词/字数: {len(self.words):,}")
        print(f"  不重复词/字数: {self.get_total_unique():,}")
        print(f"  Top {top_n} 高频词/字:")
        print("-" * 50)
        
        for i, (word, count) in enumerate(top_words, 1):
            percentage = count / len(self.words) * 100
            bar_length = int(percentage * 2)
            bar = "█" * bar_length
            print(f"  {i:2}. '{word}' → {count:4} 次 ({percentage:.2f}%) {bar}")
        print("=" * 50)
    
    @classmethod
    def quick_analyze(cls, file_path, top_n=10):
        """类方法：快速分析（一步到位）"""
        analyzer = cls(file_path)
        analyzer.load_file().clean_text().count()
        analyzer.print_report(top_n)
        return analyzer


# 测试
if __name__ == "__main__":
    # 确保有测试文件
    if not os.path.exists("data/sample.txt"):
        os.makedirs("data", exist_ok=True)
        sample_text = "大模型技术正在改变世界。大模型的应用开发是未来的趋势。" * 100
        with open("data/sample.txt", "w", encoding="utf-8") as f:
            f.write(sample_text)
    
    # 方法1：逐步调用
    print("【方法1：逐步调用】")
    analyzer = WordFrequencyAnalyzer("data/sample.txt")
    analyzer.load_file().clean_text().count()
    analyzer.print_report(top_n=10)
    
    # 方法2：快速分析
    print("\n【方法2：快速分析】")
    WordFrequencyAnalyzer.quick_analyze("data/sample.txt", top_n=5)
    
    print("\n🎉 Day 4 完成！")
