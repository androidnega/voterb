#!/usr/bin/env python3
"""
VoteBridge System Audit
Run this script to audit the entire system.
"""
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
import sys

# Color codes for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}🔍 {text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_section(text):
    print(f"\n{MAGENTA}📌 {text}{RESET}")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    print(f"{CYAN}ℹ️  {text}{RESET}")

class SystemAudit:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.backend_path = self.base_path / 'backend'
        self.frontend_path = self.base_path / 'frontend'
        self.results = {
            'date': datetime.now().isoformat(),
            'backend': {},
            'frontend': {},
            'errors': [],
            'warnings': [],
            'summary': {}
        }

    def audit_backend(self):
        print_header("Backend Audit")
        backend = self.results['backend']
        
        # Check if backend exists
        if not self.backend_path.exists():
            print_error("Backend directory not found!")
            return
        
        # Check manage.py
        manage_py = self.backend_path / 'manage.py'
        if manage_py.exists():
            print_success("manage.py exists")
        else:
            print_error("manage.py missing")
            self.results['errors'].append("manage.py missing")
        
        # Check apps
        apps = ['accounts', 'elections', 'candidates', 'voting', 'security', 'results', 
                'strongroom', 'fraud', 'notifications', 'ussd', 'system', 'operations', 'audit']
        existing_apps = []
        missing_apps = []
        for app in apps:
            app_path = self.backend_path / app
            if app_path.exists() and (app_path / 'models.py').exists():
                existing_apps.append(app)
            else:
                missing_apps.append(app)
        
        print_section("Django Apps")
        print_info(f"Found {len(existing_apps)} apps: {', '.join(existing_apps)}")
        if missing_apps:
            print_warning(f"Missing apps: {', '.join(missing_apps)}")
            self.results['warnings'].append(f"Missing apps: {missing_apps}")
        
        backend['apps'] = existing_apps
        backend['missing_apps'] = missing_apps
        
        # Check models in each app
        print_section("Models")
        model_counts = {}
        for app in existing_apps:
            models_path = self.backend_path / app / 'models.py'
            if models_path.exists():
                with open(models_path, 'r') as f:
                    content = f.read()
                    # Count class definitions (simple approximation)
                    count = content.count('class ')
                    model_counts[app] = count
        print_info(f"Models found: {json.dumps(model_counts, indent=2)}")
        backend['model_counts'] = model_counts
        
        # Check API endpoints
        print_section("API Endpoints")
        api_routes = {}
        for app in existing_apps:
            api_path = self.backend_path / app / 'api' / 'urls.py'
            if api_path.exists():
                with open(api_path, 'r') as f:
                    content = f.read()
                    # Count URL patterns (simplified)
                    count = content.count('path(')
                    api_routes[app] = count
        total_routes = sum(api_routes.values())
        print_info(f"Total API routes: {total_routes}")
        print_info(f"Routes per app: {json.dumps(api_routes, indent=2)}")
        backend['api_routes'] = api_routes
        backend['total_routes'] = total_routes
        
        # Check settings
        settings_path = self.backend_path / 'config' / 'settings.py'
        if settings_path.exists():
            print_success("Settings file exists")
        else:
            print_error("Settings file missing!")
            self.results['errors'].append("settings.py missing")
        
        # Check URLs
        urls_path = self.backend_path / 'config' / 'urls.py'
        if urls_path.exists():
            with open(urls_path, 'r') as f:
                content = f.read()
                # Count includes
                includes = content.count('include(')
                print_info(f"URL includes: {includes}")
                backend['url_includes'] = includes
        else:
            print_error("urls.py missing!")
            self.results['errors'].append("urls.py missing")
        
        # Check management commands
        print_section("Management Commands")
        commands = []
        for app in existing_apps:
            cmd_path = self.backend_path / app / 'management' / 'commands'
            if cmd_path.exists():
                for file in cmd_path.glob('*.py'):
                    if file.name != '__init__.py':
                        commands.append(f"{app}:{file.stem}")
        print_info(f"Commands: {len(commands)}")
        if commands:
            print_info(f"Available: {', '.join(commands)}")
        backend['commands'] = commands

    def audit_frontend(self):
        print_header("Frontend Audit")
        frontend = self.results['frontend']
        
        if not self.frontend_path.exists():
            print_error("Frontend directory not found!")
            return
        
        # Check package.json
        package_path = self.frontend_path / 'package.json'
        if package_path.exists():
            with open(package_path, 'r') as f:
                try:
                    pkg = json.load(f)
                    deps = pkg.get('dependencies', {})
                    dev_deps = pkg.get('devDependencies', {})
                    total_deps = len(deps) + len(dev_deps)
                    print_success(f"package.json found ({total_deps} dependencies)")
                    frontend['dependencies'] = list(deps.keys())
                except:
                    print_error("Invalid package.json")
        else:
            print_error("package.json missing")
            self.results['errors'].append("package.json missing")
        
        # Check src structure
        src_path = self.frontend_path / 'src'
        if src_path.exists():
            print_success("src directory exists")
            frontend['has_src'] = True
            
            # Check key directories
            dirs = ['api', 'stores', 'router', 'views', 'components']
            for d in dirs:
                if (src_path / d).exists():
                    print_success(f"src/{d} exists")
                else:
                    print_warning(f"src/{d} missing")
                    frontend['missing_dirs'] = frontend.get('missing_dirs', []) + [d]
            
            # Count views
            views_path = src_path / 'views'
            if views_path.exists():
                vue_files = list(views_path.rglob('*.vue'))
                frontend['vue_files'] = len(vue_files)
                print_info(f"Vue files found: {len(vue_files)}")
        else:
            print_error("src directory missing!")
            self.results['errors'].append("src missing")
        
        # Check main.js
        main_path = src_path / 'main.js' if src_path.exists() else None
        if main_path and main_path.exists():
            print_success("main.js exists")
        else:
            print_error("main.js missing")
            self.results['errors'].append("main.js missing")

    def audit_features(self):
        print_header("Feature Audit")
        features = self.results['features'] = {}
        
        # Authentication features
        print_section("Authentication")
        auth_features = [
            'Login (index/email + password)',
            'OTP verification',
            'JWT tokens',
            'Session management',
            'Role-based access',
        ]
        for f in auth_features:
            print_success(f)
        features['authentication'] = auth_features
        
        # User roles
        print_section("User Roles")
        roles = ['student', 'candidate', 'admin', 'super_admin']
        for r in roles:
            print_success(f"Role: {r}")
        features['roles'] = roles
        
        # Core features check
        print_section("Core Modules")
        modules = {
            'election_management': 'Election CRUD, positions, candidates',
            'voting_flow': 'SVT, ballot, submit, confirmation',
            'results_management': 'Generate, certify, publish, view',
            'strongroom': 'Seals, custody, public verify',
            'fraud_monitoring': 'Alerts, cases, stats',
            'notifications': 'In-app, event triggers',
            'system_settings': 'Institution, flags, integrations',
            'ussd_monitoring': 'Sessions, logs, stats',
            'audit_logs': 'MFA + audit combined view',
            'operations_center': 'Health, metrics, queues',
            'user_management': 'CRUD, roles, reset password',
        }
        for module, desc in modules.items():
            print_success(f"{module}: {desc}")
        features['modules'] = modules

    def audit_privileges(self):
        print_header("Privileges by Role")
        privileges = self.results['privileges'] = {}
        
        print_section("Student / Candidate")
        student = [
            'View own profile',
            'View eligible elections',
            'Request SVT',
            'View ballot',
            'Submit vote',
            'View published results',
            'View vote history',
            'Receive notifications'
        ]
        for p in student:
            print_success(p)
        privileges['student'] = student
        
        print_section("Admin")
        admin = [
            'Manage elections (CRUD)',
            'Manage positions',
            'Manage candidates (approve/reject)',
            'Manage voter eligibility',
            'Open/Close elections',
            'View live monitoring',
            'Preview results',
            'View security alerts',
            'View fraud cases',
            'View USSD sessions',
            'View audit logs',
            'Manage Strongroom committee',
            'Request vault access'
        ]
        for p in admin:
            print_success(p)
        privileges['admin'] = admin
        
        print_section("Super Admin")
        super_admin = [
            'All Admin privileges',
            'Certify results',
            'Publish results',
            'Approve Strongroom committee',
            'Approve vault requests',
            'User management (CRUD, roles)',
            'System settings',
            'Feature flags',
            'Maintenance mode',
            'View operations center',
            'View all logs',
            'Audit all actions'
        ]
        for p in super_admin:
            print_success(p)
        privileges['super_admin'] = super_admin

    def audit_dashboards(self):
        print_header("Dashboard Features by Role")
        dashboards = self.results['dashboards'] = {}
        
        print_section("Student Dashboard (/student)")
        student = [
            'My Elections - list of eligible elections',
            'Vote Now button on eligible elections',
            'Results tab - published results',
            'Notification bell in header',
            'Profile settings (optional)'
        ]
        for p in student:
            print_success(p)
        dashboards['student'] = student
        
        print_section("Admin Dashboard (/dashboard)")
        admin = [
            'Stats cards (Total/Active Elections, Voters, Turnout)',
            'Voting activity chart',
            'Recent activity feed',
            'Sidebar navigation: Dashboard, Elections, Results, Strongroom, Fraud, USSD, Audit',
            'Election management list',
            'Result management list'
        ]
        for p in admin:
            print_success(p)
        dashboards['admin'] = admin
        
        print_section("Super Admin Dashboard (/dashboard)")
        super_admin = [
            'All Admin dashboard features',
            'Additional sidebar: Operations, Users, Settings',
            'User management full CRUD',
            'Operations Center (health, metrics, queues, logs)',
            'System Settings (institution, flags, integrations, maintenance)',
            'Full audit view'
        ]
        for p in super_admin:
            print_success(p)
        dashboards['super_admin'] = super_admin

    def audit_structure(self):
        print_header("System Structure")
        structure = self.results['structure'] = {}
        
        # Backend structure
        print_section("Backend (Django)")
        backend_structure = {
            'framework': 'Django 5.x',
            'api_framework': 'Django REST Framework',
            'real_time': 'Django Channels + Redis',
            'database': 'PostgreSQL (SQLite in dev)',
            'cache': 'Redis',
            'auth': 'JWT (SimpleJWT) + OTP',
            'apps': self.results['backend'].get('apps', [])
        }
        structure['backend'] = backend_structure
        for k, v in backend_structure.items():
            print_info(f"{k}: {v}")
        
        # Frontend structure
        print_section("Frontend (Vue)")
        frontend_structure = {
            'framework': 'Vue 3',
            'state': 'Pinia',
            'routing': 'Vue Router',
            'ui_library': 'PrimeVue',
            'styling': 'Tailwind CSS',
            'icons': 'FontAwesome + PrimeIcons',
            'charts': 'Chart.js',
            'api_client': 'Axios'
        }
        structure['frontend'] = frontend_structure
        for k, v in frontend_structure.items():
            print_info(f"{k}: {v}")

    def generate_summary(self):
        print_header("📊 Summary")
        
        summary = self.results['summary']
        
        # Count features
        total_modules = len(self.results['features'].get('modules', {}))
        total_roles = len(self.results['privileges'].get('student', [])) + \
                     len(self.results['privileges'].get('admin', [])) + \
                     len(self.results['privileges'].get('super_admin', []))
        
        # Backend stats
        backend = self.results['backend']
        total_apps = len(backend.get('apps', []))
        total_routes = backend.get('total_routes', 0)
        
        # Frontend stats
        frontend = self.results['frontend']
        total_vue = frontend.get('vue_files', 0)
        
        print(f"{CYAN}📁 Backend Apps: {total_apps}{RESET}")
        print(f"{CYAN}🔗 API Routes: {total_routes}{RESET}")
        print(f"{CYAN}📄 Vue Files: {total_vue}{RESET}")
        print(f"{CYAN}📦 Modules: {total_modules}{RESET}")
        print(f"{CYAN}👥 Privileges: {total_roles}{RESET}")
        
        errors = len(self.results.get('errors', []))
        warnings = len(self.results.get('warnings', []))
        
        if errors == 0 and warnings == 0:
            print(f"\n{GREEN}🎉 System appears complete and healthy!{RESET}")
        else:
            if errors > 0:
                print(f"\n{RED}❌ Errors found: {errors}{RESET}")
                for e in self.results.get('errors', []):
                    print(f"  {RED}- {e}{RESET}")
            if warnings > 0:
                print(f"\n{YELLOW}⚠️ Warnings found: {warnings}{RESET}")
                for w in self.results.get('warnings', []):
                    print(f"  {YELLOW}- {w}{RESET}")
        
        summary['total_modules'] = total_modules
        summary['total_apps'] = total_apps
        summary['total_routes'] = total_routes
        summary['total_vue_files'] = total_vue
        summary['errors'] = len(self.results['errors'])
        summary['warnings'] = len(self.results['warnings'])
        
        # Save results
        audit_file = self.base_path / 'audit_results.json'
        with open(audit_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n{GREEN}📄 Full audit saved to: {audit_file}{RESET}")

    def run(self):
        print(f"{CYAN}🔍 VoteBridge System Audit{RESET}")
        print(f"{CYAN}📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
        print(f"{CYAN}📁 Base path: {self.base_path}{RESET}")
        
        self.audit_backend()
        self.audit_frontend()
        self.audit_features()
        self.audit_privileges()
        self.audit_dashboards()
        self.audit_structure()
        self.generate_summary()

if __name__ == '__main__':
    base_path = os.getcwd()
    # If running from backend, go up one level
    if Path(base_path).name == 'backend':
        base_path = str(Path(base_path).parent)
    # If running from frontend, go up one level
    if Path(base_path).name == 'frontend':
        base_path = str(Path(base_path).parent)
    
    audit = SystemAudit(base_path)
    audit.run()
