import unittest
from datetime import date
from pony.orm import *
from testutils import *

db = Database('sqlite', ':memory:')

class Department(db.Entity):
    name = Required(str)
    groups = Set('Group')
    courses = Set('Course')

class Group(db.Entity):
    number = PrimaryKey(int)
    dept = Required(Department)
    major = Required(unicode)
    students = Set("Student")

class Course(db.Entity):
    name = Required(unicode)
    dept = Required(Department)
    semester = Required(int)
    credits = Required(int)
    students = Set("Student")
    PrimaryKey(name, semester)
    
class Student(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(unicode)
    dob = Required(date)
    picture = Optional(buffer)
    gpa = Required(float, default=0)
    group = Required(Group)
    courses = Set(Course)


db.generate_mapping(create_tables=True)

class TestM2MOptimization(unittest.TestCase):
    def setUp(self):
        rollback()
    def test1(self):
        q = query(s for s in Student if len(s.courses) > 2)
        self.assertEquals(Course._table_ not in flatten(q._translator.conditions), True)
    def test2(self):
        q = query(s for s in Student if max(s.courses.semester) > 2)
        self.assertEquals(Course._table_ not in flatten(q._translator.conditions), True)
    def test3(self):
        q = query(s for s in Student if max(s.courses.credits) > 2)
        self.assertEquals(Course._table_ in flatten(q._translator.conditions), True)
        self.assertEquals(Course.students.table in flatten(q._translator.conditions), True)
    def test4(self):
        q = query(g for g in Group if sum(g.students.gpa) > 5)
        self.assertEquals(Group._table_ not in flatten(q._translator.conditions), True)
    def test5(self):
        q = query(s for s in Student if s.group.number == 1 or s.group.major == '1')
        self.assertEquals(Group._table_ in flatten(q._translator.from_), True)
    def test6(self):
        q = query(s for s in Student if s.group == Group[101])
        #fetch_all(s for s in Student if Course('1', 1) in s.courses)
        self.assertEquals(Group._table_ not in flatten(q._translator.from_), True)
    def test7(self):
        q = query(s for s in Student if sum(c.credits for c in Course if s.group.dept == c.dept) > 10)
        q.fetch_all()
        self.assertEquals(str(q._translator.from_), 
            "['FROM', ['s', 'TABLE', 'Student'], ['group-1', 'TABLE', 'Group', ['EQ', ['COLUMN', 's', 'group'], ['COLUMN', 'group-1', 'number']]]]")


if __name__ == '__main__':
    unittest.main()