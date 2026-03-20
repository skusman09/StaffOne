from app.database import SessionLocal
from app.models.onboarding import OnboardingWorkflow, OnboardingTask, EmployeeOnboarding, EmployeeTaskProgress
from app.models.user import User

def seed():
    db = SessionLocal()
    try:
        # 1. Create a Template
        template_title = "Standard Employee Onboarding"
        existing_template = db.query(OnboardingWorkflow).filter(OnboardingWorkflow.title == template_title).first()
        
        if not existing_template:
            template = OnboardingWorkflow(
                title=template_title,
                description="General onboarding tasks for all new hires at StaffOne."
            )
            db.add(template)
            db.commit()
            db.refresh(template)
            
            # Add tasks to template
            tasks = [
                OnboardingTask(workflow_id=template.id, title="Sign Employment Contract", order=1, is_required=True),
                OnboardingTask(workflow_id=template.id, title="Submit ID Proofs", order=2, is_required=True),
                OnboardingTask(workflow_id=template.id, title="Attend HR Orientation", order=3, is_required=True),
                OnboardingTask(workflow_id=template.id, title="Setup System & Software", order=4, is_required=True),
            ]
            db.add_all(tasks)
            db.commit()
            print(f"Template '{template_title}' created.")
        else:
            template = existing_template
            print(f"Template '{template_title}' already exists.")

        # 2. Assign to the first user
        user = db.query(User).first()
        if not user:
            from app.core.config import settings
            from app.services.auth_service import get_password_hash
            user = User(
                email="test@staffone.com",
                username="testuser",
                hashed_password="hashed_password", # Simplified for seeding
                full_name="Test User",
                role="employee",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print("Created test user: testuser")

        if user:
            existing_onboarding = db.query(EmployeeOnboarding).filter(
                EmployeeOnboarding.user_id == user.id,
                EmployeeOnboarding.workflow_id == template.id
            ).first()

            if not existing_onboarding:
                emp_ob = EmployeeOnboarding(user_id=user.id, workflow_id=template.id)
                db.add(emp_ob)
                db.commit()
                db.refresh(emp_ob)

                # Add progress tracking
                workflow_tasks = db.query(OnboardingTask).filter(OnboardingTask.workflow_id == template.id).all()
                progress = [
                    EmployeeTaskProgress(employee_onboarding_id=emp_ob.id, task_id=t.id)
                    for t in workflow_tasks
                ]
                db.add_all(progress)
                db.commit()
                print(f"Onboarding assigned to user: {user.username}")
            else:
                print(f"Onboarding already assigned to user: {user.username}")
        else:
            print("No users found to assign onboarding.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding onboarding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
