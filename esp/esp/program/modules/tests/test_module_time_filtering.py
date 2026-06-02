from django.test import TestCase
from esp.program.models import Program, ProgramModule, ClassRegModuleInfo, StudentClassRegModuleInfo
from esp.program.modules.models import ProgramModuleObj
from esp.users.models import ESPUser
import datetime

class TestModuleTimeFiltering(TestCase):
    def setUp(self):
        # Create a program
        self.program = Program.objects.create(
            name="Test Program",
            program_type="test",
            url="testprog"
        )
        
        # Create necessary info objects for the program
        ClassRegModuleInfo.objects.create(program=self.program)
        StudentClassRegModuleInfo.objects.create(program=self.program)

        # Create a standard user (student)
        self.student = ESPUser.objects.create_user(username='student_test', email='student@test.com', password='password')
        
        # Create an admin user
        self.admin = ESPUser.objects.create_user(username='admin_test', email='admin@test.com', password='password')
        self.admin.makeAdmin()

        # Create base module definition
        self.base_module = ProgramModule.objects.create(
            module_type="learn",
            handler="SomeModule"
        )

        now = datetime.datetime.now()
        self.past = now - datetime.timedelta(days=1)
        self.future = now + datetime.timedelta(days=1)

    def _create_module_obj(self, start=None, end=None):
        return ProgramModuleObj.objects.create(
            program=self.program,
            module=self.base_module,
            start_date=start,
            end_date=end
        )

    def test_active_module_visible_to_student(self):
        """A module that has started and not ended should be visible to students."""
        mod = self._create_module_obj(start=self.past, end=self.future)
        
        modules = self.program.getModules(user=self.student)
        self.assertIn(mod, modules)

    def test_null_dates_module_visible_to_student(self):
        """A module with no start/end dates (default) should be visible to students."""
        mod = self._create_module_obj(start=None, end=None)
        
        modules = self.program.getModules(user=self.student)
        self.assertIn(mod, modules)

    def test_expired_module_hidden_from_student(self):
        """A module that has ended should be hidden from students."""
        mod = self._create_module_obj(start=None, end=self.past)
        
        modules = self.program.getModules(user=self.student)
        self.assertNotIn(mod, modules)

    def test_future_module_hidden_from_student(self):
        """A module that hasn't started yet should be hidden from students."""
        mod = self._create_module_obj(start=self.future, end=None)
        
        modules = self.program.getModules(user=self.student)
        self.assertNotIn(mod, modules)

    def test_expired_module_visible_to_admin(self):
        """Admins bypass time filtering and can see expired modules."""
        mod = self._create_module_obj(start=None, end=self.past)
        
        modules = self.program.getModules(user=self.admin)
        self.assertIn(mod, modules)

    def test_future_module_visible_to_admin(self):
        """Admins bypass time filtering and can see future modules."""
        mod = self._create_module_obj(start=self.future, end=None)
        
        modules = self.program.getModules(user=self.admin)
        self.assertIn(mod, modules)

    def test_no_user_returns_all_modules(self):
        """Internal calls without a user object bypass filtering entirely."""
        mod_expired = self._create_module_obj(start=None, end=self.past)
        mod_future = self._create_module_obj(start=self.future, end=None)
        
        # When getModules is called internally without user attached
        modules = self.program.getModules(user=None)
        
        self.assertIn(mod_expired, modules)
        self.assertIn(mod_future, modules)
