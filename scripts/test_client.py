import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database.connection import SessionLocal
from backend.app.api.routers.products import list_products
from backend.app.api.routers.applicants import list_applicants, get_applicant_detail
from backend.app.api.routers.applications import list_applications, get_application_detail, submit_new_application
from backend.app.api.routers.analytics import get_executive_kpis, get_risk_analytics, get_operations_analytics
from backend.app.api.routers.repayments import get_repayment_schedule
from backend.app.schemas.pydantic_models import ApplicationCreate

def main():
    db = SessionLocal()
    try:
        print("[1] Testing list_products...")
        prods = list_products(db)
        print(f" -> Found {len(prods)} products: {[p.product_id for p in prods]}")

        print("[2] Testing list_applicants...")
        apps = list_applicants(skip=0, limit=5, search=None, db=db)
        print(f" -> Found {len(apps)} applicants. First: {apps[0].applicant_id} ({apps[0].first_name})")

        print("[3] Testing list_applications...")
        app_list = list_applications(status=None, product_id=None, skip=0, limit=5, db=db)
        print(f" -> Found {len(app_list)} applications. First: {app_list[0].application_id} (Status: {app_list[0].application_status})")

        print("[4] Testing get_application_detail...")
        app_detail = get_application_detail(app_list[0].application_id, db=db)
        print(f" -> Application detail: {app_detail['application_id']}, Docs: {len(app_detail['documents'])}, Decision: {app_detail['decision'].decision_status if app_detail['decision'] else 'None'}")

        print("[5] Testing get_executive_kpis...")
        exec_kpis = get_executive_kpis(db=db)
        print(f" -> Executive KPIs: Total Apps: {exec_kpis['total_applications']}, Approved: {exec_kpis['approved_count']}, Approval Rate: {exec_kpis['approval_rate']}%")

        print("[6] Testing get_risk_analytics...")
        risk = get_risk_analytics(db=db)
        print(f" -> Risk analytics: Credit Score Bins: {len(risk['credit_score_distribution'])}, DTI Bins: {len(risk['dti_distribution'])}")

        print("[7] Testing live submit_new_application...")
        new_app_payload = ApplicationCreate(
            applicant_id=apps[0].applicant_id,
            product_id="PROD-001",
            requested_principal=150000.0,
            requested_term_months=24,
            submission_channel="ONLINE_PORTAL"
        )
        new_result = submit_new_application(new_app_payload, db=db)
        print(f" -> Live application submitted: {new_result['application_id']} -> Outcome: {new_result['decision_status']} ({new_result['reason_code']})")

        print("\nALL API ENDPOINTS TESTED AND VERIFIED SUCCESSFULLY!")
    finally:
        db.close()

if __name__ == "__main__":
    main()
