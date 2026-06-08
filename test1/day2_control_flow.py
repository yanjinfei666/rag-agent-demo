"""
Day 2：if/else、for/while、函数
实战：学生成绩管理控制台程序（升级版）
"""

# ============ 1. if/elif/else 条件判断 ============
print("=" * 20, "条件判断", "=" * 20)

def get_grade_level(score):
    """根据分数返回等级"""
    if score >= 90:
        return "优秀"
    elif score >= 80:
        return "良好"
    elif score >= 60:
        return "及格"
    else:
        return "不及格"

# 测试不同分数
for test_score in [95, 82, 60, 45]:
    print(f"{test_score}分 → {get_grade_level(test_score)}")


# ============ 2. for 循环 ============
print("\n" + "=" * 20, "for循环", "=" * 20)

# 遍历列表
fruits = ["苹果", "香蕉", "橘子", "葡萄"]
for i, fruit in enumerate(fruits, 1):
    print(f"第{i}个水果: {fruit}")

# 遍历字典
student_scores = {"张三": 90, "李四": 85, "王五": 78}
print("\n成绩单:")
for name, score in student_scores.items():
    print(f"{name}: {score}分 - {get_grade_level(score)}")


# ============ 3. while 循环 ============
print("\n" + "=" * 20, "while循环", "=" * 20)

def countdown(n):
    """倒计时函数"""
    3

    
    while n > 0:
        print(f"倒计时: {n}")
        n -= 1
    print("开始！")

countdown(3)


# ============ 4. 函数参数类型 ============
print("\n" + "=" * 20, "函数参数", "=" * 20)

def introduce(name, age, city="未知", *hobbies, **extra):
    """
    演示各种参数类型
    name: 位置参数（必填）
    age: 位置参数（必填）
    city: 默认参数（可选）
    *hobbies: 可变位置参数
    **extra: 可变关键字参数
    """
    print(f"姓名: {name}")
    print(f"年龄: {age}")
    print(f"城市: {city}")
    if hobbies:
        print(f"爱好: {', '.join(hobbies)}")
    if extra:
        print(f"其他信息: {extra}")

# 调用演示
introduce("张三", 20)
print("---")
introduce("李四", 22, "北京", "编程", "篮球", 身高="180cm", 专业="计算机")


# ============ 5. 综合实战：学生成绩管理系统（完整版）============
print("\n" + "=" * 20, "学生成绩管理系统", "=" * 20)

class StudentManager:
    """学生成绩管理器"""
    
    def __init__(self):
        self.students = []
    
    def add(self, name, score):
        """添加学生"""
        if not isinstance(score, (int, float)):
            print(f"❌ 分数必须是数字")
            return False
        if score < 0 or score > 100:
            print(f"❌ 分数必须在0-100之间")
            return False
        self.students.append({"name": name, "score": score})
        print(f"✓ 添加成功: {name} - {score}分")
        return True
    
    def remove(self, name):
        """删除学生"""
        for i, s in enumerate(self.students):
            if s["name"] == name:
                del self.students[i]
                print(f"✓ 已删除: {name}")
                return True
        print(f"❌ 未找到学生: {name}")
        return False
    
    def search(self, name):
        """查找学生"""
        for s in self.students:
            if s["name"] == name:
                return s
        return None
    
    def get_avg_score(self):
        """计算平均分"""
        if not self.students:
            return 0
        return sum(s["score"] for s in self.students) / len(self.students)
    
    def get_max_score_student(self):
        """获取最高分学生"""
        if not self.students:
            return None
        return max(self.students, key=lambda x: x["score"])
    
    def get_pass_rate(self):
        """计算及格率"""
        if not self.students:
            return 0
        pass_count = sum(1 for s in self.students if s["score"] >= 60)
        return pass_count / len(self.students) * 100
    
    def show_all(self):
        """显示所有学生"""
        if not self.students:
            print("暂无学生数据")
            return
        print("\n" + "=" * 40)
        print(f"{'姓名':<10} {'分数':<10} {'等级':<10}")
        print("-" * 40)
        for s in self.students:
            print(f"{s['name']:<10} {s['score']:<10} {get_grade_level(s['score']):<10}")
        print("-" * 40)
        print(f"总人数: {len(self.students)}")
        print(f"平均分: {self.get_avg_score():.1f}")
        print(f"及格率: {self.get_pass_rate():.1f}%")
        best = self.get_max_score_student()
        if best:
            print(f"最高分: {best['name']} - {best['score']}分")
        print("=" * 40)


# 测试整个系统
if __name__ == "__main__":
    manager = StudentManager()
    
    # 添加学生
    manager.add("张三", 90)
    manager.add("李四", 85)
    manager.add("王五", 55)
    manager.add("赵六", 78)
    manager.add("钱七", 95)
    
    # 显示全部
    manager.show_all()
    
    # 查找测试
    result = manager.search("张三")
    print(f"\n查找张三: {result}")
    
    # 删除测试
    manager.remove("王五")
    manager.show_all()
    
    print("\n🎉 Day 2 完成！")
