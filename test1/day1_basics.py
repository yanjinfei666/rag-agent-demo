"""
Day 1：Python基础与数据结构
目标：熟练操作list和dict，并运行一个综合脚本
"""

# ============ 1. List 增删改查 ============
print("=" * 20, "列表操作", "=" * 20)

students = ["Alice", "Bob", "Cindy"]
print("原始列表:", students)

# 增
students.append("David")
students.insert(1, "Eric")
print("增加后:", students)

# 删
students.remove("Bob")
removed_student = students.pop(0)
print(f"被移除的学生: {removed_student}")
print("删除后:", students)

# 改
students[0] = "Alice Smith"
print("修改后:", students)

# 查（列表推导式）
long_names = [s for s in students if len(s) > 4]
print("名字长度>4的学生:", long_names)


# ============ 2. Dictionary 增删改查 ============
print("\n" + "=" * 20, "字典操作", "=" * 20)

grades = {"Alice": 85, "Bob": 92, "Cindy": 78}
print("原始成绩单:", grades)

# 增
grades["David"] = 88
# 改
grades["Alice"] = 90
print("更新后:", grades)

# 删
removed = grades.pop("Cindy")
print(f"移除的分数: {removed}")

# 查
high_scorers = {k: v for k, v in grades.items() if v > 80}
print("高分学生:", high_scorers)


# ============ 3. 综合实战：学生成绩管理系统 ============
print("\n" + "=" * 20, "简易成绩系统", "=" * 20)

student_db = []

def add_student(name, score):
    if not isinstance(score, (int, float)) or not (0 <= score <= 100):
        print(f"错误：分数必须是0-100之间的数字，你输入的是{score}")
        return
    student_db.append({"name": name, "score": score})
    print(f"✓ 已添加: {name}, 成绩: {score}")

def get_avg():
    if not student_db:
        return 0
    return sum(s["score"] for s in student_db) / len(student_db)

def show_all():
    if not student_db:
        print("暂无学生数据")
        return
    print("\n当前所有学生:")
    for i, s in enumerate(student_db, 1):
        print(f"  {i}. {s['name']}: {s['score']}分")
    print(f"班级平均分: {get_avg():.1f}")

# 测试
add_student("张三", 90)
add_student("李四", 85)
add_student("王五", 105)  # 应该报错
add_student("赵六", 78)
show_all()

print("\n🎉 Day 1 完成！")
