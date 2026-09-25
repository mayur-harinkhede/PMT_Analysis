import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_cmms_dataset():
    """
    Generates a synchronized, realistic dataset mapping all schema tables with:
    - Dedicated 'TODAY' tickets with real-time delays, work started, actions taken, MTTR, and verification delays.
    - Historical tickets (1-30 days ago).
    - Unregistered / Custom equipment cases (`custom_equipment`).
    - PM vs CM schedules (`rep_preventive_machine_schedule`, `preventive_maintenance_checklist`).
    - Tool holding times ($return_time - taken_time$) and hoarded/overdue tools.
    - Spare parts pricing, critical spare consumption, and stockout alerts.
    - Status lifecycle transitions (`ticket_status_history`) with stage durations.
    """
    np.random.seed(42)
    now = datetime.now()
    today_date = now.date()

    # 1. Clusters & Kitchens
    clusters = [
        {"id": "cl-1", "name": "North Industrial Zone", "created_at": now - timedelta(days=120)},
        {"id": "cl-2", "name": "South Mega Kitchen Cluster", "created_at": now - timedelta(days=120)},
        {"id": "cl-3", "name": "West Bakery & Ready Foods Hub", "created_at": now - timedelta(days=120)}
    ]
    df_clusters = pd.DataFrame(clusters)

    kitchens = [
        {"id": "k-1", "cluster_id": "cl-1", "name": "Central Production Unit - North", "address": "Plot 12, Industrial Sector 4", "status": True, "created_at": now - timedelta(days=100)},
        {"id": "k-2", "cluster_id": "cl-2", "name": "Main Kitchen - South", "address": "Hub 5, South Corridor", "status": True, "created_at": now - timedelta(days=100)},
        {"id": "k-3", "cluster_id": "cl-3", "name": "Bakery & Confectionery - West", "address": "Unit 8, Food Park", "status": True, "created_at": now - timedelta(days=100)},
        {"id": "k-4", "cluster_id": "cl-1", "name": "QSR Commissary - East", "address": "Bay 3, Metro Hub", "status": True, "created_at": now - timedelta(days=100)}
    ]
    df_kitchens = pd.DataFrame(kitchens)

    # 2. Zones & Areas
    zones = [
        {"id": "z-1", "kitchen_id": "k-1", "name": "Boiler & Steam Utilities", "telegram_chat_id": "-1001234567890", "status": True},
        {"id": "z-2", "kitchen_id": "k-1", "name": "Cold Storage & Refrigeration", "telegram_chat_id": "-1001234567891", "status": True},
        {"id": "z-3", "kitchen_id": "k-2", "name": "Dishwashing & Hygiene Area", "telegram_chat_id": "-1001234567892", "status": True},
        {"id": "z-4", "kitchen_id": "k-2", "name": "Main Hot Cooking Line", "telegram_chat_id": "-1001234567893", "status": True},
        {"id": "z-5", "kitchen_id": "k-3", "name": "Dough Preparation & Mixing", "telegram_chat_id": "-1001234567894", "status": True},
        {"id": "z-6", "kitchen_id": "k-3", "name": "Rotary Ovens & Baking", "telegram_chat_id": "-1001234567895", "status": True},
        {"id": "z-7", "kitchen_id": "k-4", "name": "Deep Frying & Batch Cooking", "telegram_chat_id": "-1001234567896", "status": True}
    ]
    df_zones = pd.DataFrame(zones)

    areas = [
        {"id": "a-1", "zone_id": "z-1", "area_name": "Steam Header Room", "status": True},
        {"id": "a-2", "zone_id": "z-2", "area_name": "Deep Freezer Bay #1", "status": True},
        {"id": "a-3", "zone_id": "z-3", "area_name": "Flight Washer Conveyor Line", "status": True},
        {"id": "a-4", "zone_id": "z-4", "area_name": "Steam Jacketed Kettles Line", "status": True},
        {"id": "a-5", "zone_id": "z-5", "area_name": "Spiral Mixer Station", "status": True},
        {"id": "a-6", "zone_id": "z-6", "area_name": "Deck Oven Bank", "status": True},
        {"id": "a-7", "zone_id": "z-7", "area_name": "Automatic Pressure Fryer Deck", "status": True}
    ]
    df_areas = pd.DataFrame(areas)

    # 3. Users
    users = [
        {"id": "u-1", "amp_id": "AMP-8001", "name": "David Miller", "role": "admin", "department": "Plant Engineering", "mobile_no": "+919876543201", "status": True},
        {"id": "u-2", "amp_id": "AMP-8021", "name": "Arun Sharma", "role": "technician", "department": "Mechanical & Steam", "mobile_no": "+919876543202", "status": True},
        {"id": "u-3", "amp_id": "AMP-8045", "name": "Karthik Raj", "role": "technician", "department": "Electrical & Controls", "mobile_no": "+919876543203", "status": True},
        {"id": "u-4", "amp_id": "AMP-8090", "name": "Vikram Das", "role": "technician", "department": "HVAC & Refrigeration", "mobile_no": "+919876543204", "status": True},
        {"id": "u-5", "amp_id": "AMP-7101", "name": "Rajesh Kumar", "role": "raiser", "department": "Operations", "mobile_no": "+919876543205", "status": True},
        {"id": "u-6", "amp_id": "AMP-7102", "name": "Pooja Singh", "role": "raiser", "department": "Bakery", "mobile_no": "+919876543206", "status": True},
        {"id": "u-7", "amp_id": "AMP-7103", "name": "Sunil Verma", "role": "raiser", "department": "Hygiene", "mobile_no": "+919876543207", "status": True},
        {"id": "u-8", "amp_id": "AMP-7104", "name": "Farhan Ali", "role": "raiser", "department": "Kitchen Production", "mobile_no": "+919876543208", "status": True}
    ]
    df_users = pd.DataFrame(users)

    # 4. Equipment
    equipments = [
        {"id": "eq-1", "equipment_code": "EQ-BLR-001", "name": "Industrial Steam Boiler 500kg/hr", "model": "Thermax CP-500", "area_id": "a-1", "status": True, "date_of_commision": "2023-01-15", "remarks": "Primary Steam Generator"},
        {"id": "eq-2", "equipment_code": "EQ-CLD-002", "name": "Walk-In Deep Freezer Room #2", "model": "Bluestar BDF-3000", "area_id": "a-2", "status": True, "date_of_commision": "2023-04-10", "remarks": "Set point -18C"},
        {"id": "eq-3", "equipment_code": "EQ-DSH-003", "name": "Conveyor Flight Dishwasher", "model": "Hobart Pro-2400", "area_id": "a-3", "status": True, "date_of_commision": "2023-06-20", "remarks": "Sanitization line"},
        {"id": "eq-4", "equipment_code": "EQ-MIX-004", "name": "Spiral Dough Mixer 120L", "model": "Sinmag SM-120", "area_id": "a-5", "status": True, "date_of_commision": "2023-08-12", "remarks": "High-torque bakery mixer"},
        {"id": "eq-5", "equipment_code": "EQ-IND-011", "name": "Commercial Induction Range 5KW", "model": "Electrolux Ind-500", "area_id": "a-4", "status": True, "date_of_commision": "2024-02-01", "remarks": "Hot kitchen"},
        {"id": "eq-6", "equipment_code": "EQ-FRY-007", "name": "Continuous Conveyor Deep Fryer", "model": "Frymaster Pro-80", "area_id": "a-7", "status": True, "date_of_commision": "2024-01-18", "remarks": "High production frying"},
        {"id": "eq-7", "equipment_code": "EQ-RO-001", "name": "Industrial RO Water Plant 1000 LPH", "model": "Pentair RO-1000", "area_id": "a-1", "status": True, "date_of_commision": "2023-03-05", "remarks": "Boiler feed & cooking water"}
    ]
    df_equipments = pd.DataFrame(equipments)

    # 5. Spares & Spares Tracker with Unit Cost
    spares = [
        {"id": "sp-1", "kitchen_id": "k-1", "spare_code": "SPR-GST-09", "spare_name": "High-Temp Pressure Gasket 40mm", "spare_type": "Mechanical", "is_critical": True, "uom": "PCS", "unit_cost": 450.0, "status": True},
        {"id": "sp-2", "kitchen_id": "k-1", "spare_code": "SPR-GAS-404", "spare_name": "R404A Refrigerant Gas Cylinder 10kg", "spare_type": "Refrigeration", "is_critical": True, "uom": "CAN", "unit_cost": 5200.0, "status": True},
        {"id": "sp-3", "kitchen_id": "k-2", "spare_code": "SPR-SL-22", "spare_name": "Silicon Pump Shaft Seal 22mm", "spare_type": "Plumbing", "is_critical": False, "uom": "PCS", "unit_cost": 380.0, "status": True},
        {"id": "sp-4", "kitchen_id": "k-3", "spare_code": "SPR-BRG-12", "spare_name": "Heavy Duty Ball Bearing 6205-2RS", "spare_type": "Mechanical", "is_critical": False, "uom": "PCS", "unit_cost": 650.0, "status": True},
        {"id": "sp-5", "kitchen_id": "k-4", "spare_code": "SPR-SNS-10", "spare_name": "Thermostat Sensor 250V Probe", "spare_type": "Electrical", "is_critical": True, "uom": "PCS", "unit_cost": 1200.0, "status": True},
        {"id": "sp-6", "kitchen_id": "k-1", "spare_code": "SPR-VLV-04", "spare_name": "Pneumatic Solenoid Valve 24V DC", "spare_type": "Instrumentation", "is_critical": True, "uom": "PCS", "unit_cost": 2100.0, "status": True},
        {"id": "sp-7", "kitchen_id": "k-2", "spare_code": "SPR-HTR-15", "spare_name": "Boiler Immersion Heating Element 3KW", "spare_type": "Electrical", "is_critical": True, "uom": "PCS", "unit_cost": 3400.0, "status": True}
    ]
    df_spares = pd.DataFrame(spares)

    spare_trackers = [
        {"id": "st-1", "spare_id": "sp-1", "current_qty": 8, "total_qty": 20, "min_qty_alert": 4, "last_updated": now - timedelta(days=2)},
        {"id": "st-2", "spare_id": "sp-2", "current_qty": 1, "total_qty": 5, "min_qty_alert": 3, "last_updated": now - timedelta(days=1)}, # Critical Alert!
        {"id": "st-3", "spare_id": "sp-3", "current_qty": 12, "total_qty": 15, "min_qty_alert": 5, "last_updated": now - timedelta(days=3)},
        {"id": "st-4", "spare_id": "sp-4", "current_qty": 15, "total_qty": 25, "min_qty_alert": 6, "last_updated": now - timedelta(days=4)},
        {"id": "st-5", "spare_id": "sp-5", "current_qty": 2, "total_qty": 10, "min_qty_alert": 3, "last_updated": now - timedelta(hours=6)}, # Low Stock!
        {"id": "st-6", "spare_id": "sp-6", "current_qty": 4, "total_qty": 8, "min_qty_alert": 2, "last_updated": now - timedelta(days=5)},
        {"id": "st-7", "spare_id": "sp-7", "current_qty": 2, "total_qty": 6, "min_qty_alert": 2, "last_updated": now - timedelta(days=1)}
    ]
    df_spare_tracker = pd.DataFrame(spare_trackers)

    # 6. Tools
    tools = [
        {"id": "tl-1", "tool_name": "Hydraulic Torque Wrench 300Nm", "kitchen_id": "k-1", "status": True},
        {"id": "tl-2", "tool_name": "Fluke 87V True-RMS Digital Multimeter", "kitchen_id": "k-4", "status": True},
        {"id": "tl-3", "tool_name": "Digital Refrigeration Manifold Gauge Kit", "kitchen_id": "k-1", "status": True},
        {"id": "tl-4", "tool_name": "Heavy Duty 3-Jaw Bearing Puller Kit", "kitchen_id": "k-3", "status": True},
        {"id": "tl-5", "tool_name": "Laser Infrared Thermometer / Pyrometer", "kitchen_id": "k-2", "status": True}
    ]
    df_tools = pd.DataFrame(tools)

    # 7. Comprehensive Tickets Generation (Explicitly including TODAY's active shift tickets!)
    ticket_data = []
    ticket_status_history = []
    ticket_spares = []
    ticket_tools_data = []
    ticket_media_data = []

    # A. TODAY'S TICKETS (Realistic live shift tickets for today)
    today_tickets_pool = [
        {
            "ticket_no": f"TCK-{today_date.strftime('%Y%m%d')}-01",
            "title": "Steam Boiler High Pressure Relief Valve Tripping",
            "cause_of_issue": "Calcification and scale build-up inside primary relief nozzle",
            "category": "Steam / Boiler",
            "priority": "CRITICAL",
            "status": "VERIFIED",
            "kitchen_id": "k-1",
            "area_id": "a-1",
            "equipment_id": "eq-1",
            "custom_equipment": None,
            "raised_by_id": "u-5",
            "assigned_to_id": "u-2",
            "verified_by_id": "u-1",
            "breakdown_offset_mins": 300, # 5 hours ago
            "raised_offset_mins": 280,     # raised 4h 40m ago
            "work_start_offset_mins": 240, # work started 4h ago (Delay = 40 mins)
            "completion_offset_mins": 90,  # completed 1.5h ago (MTTR = 150 mins / 2.5h)
            "raiser_ver_offset_mins": 60,  # verified by raiser 30 mins after completion
            "admin_ver_offset_mins": 20,   # verified by admin 70 mins after completion
            "action_taken": "De-scaled nozzle with chemical flush, replaced PTFE sealing gasket and calibrated safety trip pressure to 8.2 bar.",
            "spares_used": [("sp-1", 2)],
            "tool_issued": ("tl-1", True, 150),
            "media": ["BEFORE_REPAIR", "AFTER_REPAIR"]
        },
        {
            "ticket_no": f"TCK-{today_date.strftime('%Y%m%d')}-02",
            "title": "Dough Mixer Motor Overheating & Tripping MCB",
            "cause_of_issue": "Bearing seized due to flour dust ingress and lack of lubrication",
            "category": "Mechanical",
            "priority": "HIGH",
            "status": "IN_PROGRESS",
            "kitchen_id": "k-3",
            "area_id": "a-5",
            "equipment_id": "eq-4",
            "custom_equipment": None,
            "raised_by_id": "u-6",
            "assigned_to_id": "u-3",
            "verified_by_id": None,
            "breakdown_offset_mins": 190,
            "raised_offset_mins": 175,
            "work_start_offset_mins": 110, # Delay = 65 mins (High Delay alert!)
            "completion_offset_mins": None, # In progress
            "raiser_ver_offset_mins": None,
            "admin_ver_offset_mins": None,
            "action_taken": "Disassembled motor bracket, extracted damaged bearing 6205-2RS, cleaning drive shaft housing.",
            "spares_used": [("sp-4", 1)],
            "tool_issued": ("tl-4", False, None), # Tool held!
            "media": ["BEFORE_REPAIR"]
        },
        {
            "ticket_no": f"TCK-{today_date.strftime('%Y%m%d')}-03",
            "title": "Walk-in Freezer Temperature Spike (+4°C vs -18°C Setpoint)",
            "cause_of_issue": "Refrigerant line capillary clog and condenser fan motor stalled",
            "category": "Refrigeration",
            "priority": "CRITICAL",
            "status": "PENDING_SPARES",
            "kitchen_id": "k-1",
            "area_id": "a-2",
            "equipment_id": "eq-2",
            "custom_equipment": None,
            "raised_by_id": "u-5",
            "assigned_to_id": "u-4",
            "verified_by_id": None,
            "breakdown_offset_mins": 250,
            "raised_offset_mins": 235,
            "work_start_offset_mins": 210, # Delay = 25 mins
            "completion_offset_mins": None,
            "raiser_ver_offset_mins": None,
            "admin_ver_offset_mins": None,
            "action_taken": "Diagnosed low suction pressure. Stockout on R404A canister, requested urgent purchase from vendor.",
            "spares_used": [("sp-2", 1)],
            "tool_issued": ("tl-3", False, None), # Tool held!
            "media": ["BEFORE_REPAIR"]
        },
        {
            "ticket_no": f"TCK-{today_date.strftime('%Y%m%d')}-04",
            "title": "Commercial Dishwasher Wash Cycle Low Pressure",
            "cause_of_issue": "Impeller clogged with food debris & worn booster shaft seal",
            "category": "Plumbing & RO",
            "priority": "MEDIUM",
            "status": "COMPLETED",
            "kitchen_id": "k-2",
            "area_id": "a-3",
            "equipment_id": "eq-3",
            "custom_equipment": None,
            "raised_by_id": "u-7",
            "assigned_to_id": "u-2",
            "verified_by_id": None,
            "breakdown_offset_mins": 220,
            "raised_offset_mins": 200,
            "work_start_offset_mins": 160, # Delay = 40 mins
            "completion_offset_mins": 45,  # Completed 45m ago (MTTR = 115 mins)
            "raiser_ver_offset_mins": 15,  # Raiser verified 30m after completion
            "admin_ver_offset_mins": None, # Admin verification pending!
            "action_taken": "Cleaned wash arms, replaced mechanical shaft seal 22mm, tested wash cycle pressure at 2.5 bar.",
            "spares_used": [("sp-3", 1)],
            "tool_issued": ("tl-5", True, 115),
            "media": ["BEFORE_REPAIR", "AFTER_REPAIR"]
        },
        {
            "ticket_no": f"TCK-{today_date.strftime('%Y%m%d')}-05",
            "title": "Local Dough Sheeter Roller Jam (Unregistered Unit)",
            "cause_of_issue": "Nylon drive gear stripped on non-standard pastry sheeter",
            "category": "Mechanical",
            "priority": "HIGH",
            "status": "OPEN",
            "kitchen_id": "k-3",
            "area_id": "a-5",
            "equipment_id": None, # Unregistered Equipment!
            "custom_equipment": "Vendor Portable Dough Sheeter (Non-Asset)",
            "raised_by_id": "u-6",
            "assigned_to_id": None, # Not yet assigned (Pending dispatch)
            "verified_by_id": None,
            "breakdown_offset_mins": 45,
            "raised_offset_mins": 35,
            "work_start_offset_mins": None, # Work not started!
            "completion_offset_mins": None,
            "raiser_ver_offset_mins": None,
            "admin_ver_offset_mins": None,
            "action_taken": "Awaiting technician assignment to evaluate local gearbox spare availability.",
            "spares_used": [],
            "tool_issued": None,
            "media": []
        },
        {
            "ticket_no": f"TCK-{today_date.strftime('%Y%m%d')}-06",
            "title": "Main Induction Cooktop Error Code E-04",
            "cause_of_issue": "IGBT power module thermal sensor short circuit",
            "category": "Electrical",
            "priority": "HIGH",
            "status": "VERIFIED",
            "kitchen_id": "k-4",
            "area_id": "a-4",
            "equipment_id": "eq-5",
            "custom_equipment": None,
            "raised_by_id": "u-8",
            "assigned_to_id": "u-3",
            "verified_by_id": "u-1",
            "breakdown_offset_mins": 360,
            "raised_offset_mins": 345,
            "work_start_offset_mins": 310, # Delay = 35 mins
            "completion_offset_mins": 190, # MTTR = 120 mins
            "raiser_ver_offset_mins": 160, # Raiser verified (30m delay)
            "admin_ver_offset_mins": 100, # Admin verified (90m delay)
            "action_taken": "Replaced IGBT sensor probe, reapplied thermal compound, validated current draw at 20A.",
            "spares_used": [("sp-5", 1)],
            "tool_issued": ("tl-2", True, 120),
            "media": ["AFTER_REPAIR"]
        }
    ]

    # Process Today's Tickets
    for idx, item in enumerate(today_tickets_pool, start=1):
        t_id = f"tck-today-{idx:02d}"
        bd_time = now - timedelta(minutes=item["breakdown_offset_mins"]) if item["breakdown_offset_mins"] else None
        raised_time = now - timedelta(minutes=item["raised_offset_mins"]) if item["raised_offset_mins"] else None
        repair_start = now - timedelta(minutes=item["work_start_offset_mins"]) if item["work_start_offset_mins"] else None
        completion_time = now - timedelta(minutes=item["completion_offset_mins"]) if item["completion_offset_mins"] else None
        
        raiser_ver = item["raiser_ver_offset_mins"] is not None
        raiser_ver_time = (now - timedelta(minutes=item["raiser_ver_offset_mins"])) if raiser_ver else None
        
        admin_ver = item["admin_ver_offset_mins"] is not None
        admin_ver_time = (now - timedelta(minutes=item["admin_ver_offset_mins"])) if admin_ver else None

        ticket_data.append({
            "id": t_id,
            "ticket_no": item["ticket_no"],
            "title": item["title"],
            "cause_of_issue": item["cause_of_issue"],
            "category": item["category"],
            "priority": item["priority"],
            "status": item["status"],
            "kitchen_id": item["kitchen_id"],
            "area_id": item["area_id"],
            "equipment_id": item["equipment_id"],
            "custom_equipment": item["custom_equipment"],
            "raised_by_id": item["raised_by_id"],
            "assigned_to_id": item["assigned_to_id"],
            "verified_by_id": item["verified_by_id"],
            "breakdown_time": bd_time,
            "ticket_raised_time": raised_time,
            "repair_start_time": repair_start,
            "ticket_completion_time": completion_time,
            "updated_at": completion_time or repair_start or raised_time,
            "admin_verified": admin_ver,
            "admin_verified_at": admin_ver_time,
            "raiser_verified": raiser_ver,
            "raiser_verified_at": raiser_ver_time,
            "action_taken": item["action_taken"],
            "telegram_message_id": f"msg_tg_today_{idx}"
        })

        # History timeline
        ticket_status_history.append({
            "id": f"tsh-today-{idx}-1", "ticket_id": t_id, "changed_by": item["raised_by_id"], "from_status": None, "to_status": "OPEN", "created_at": raised_time
        })
        if repair_start:
            ticket_status_history.append({
                "id": f"tsh-today-{idx}-2", "ticket_id": t_id, "changed_by": item["assigned_to_id"], "from_status": "OPEN", "to_status": "IN_PROGRESS", "created_at": repair_start
            })
        if item["status"] == "PENDING_SPARES":
            ticket_status_history.append({
                "id": f"tsh-today-{idx}-3", "ticket_id": t_id, "changed_by": item["assigned_to_id"], "from_status": "IN_PROGRESS", "to_status": "PENDING_SPARES", "created_at": repair_start + timedelta(minutes=20)
            })
        if completion_time:
            ticket_status_history.append({
                "id": f"tsh-today-{idx}-4", "ticket_id": t_id, "changed_by": item["assigned_to_id"], "from_status": "IN_PROGRESS", "to_status": "COMPLETED", "created_at": completion_time
            })
        if admin_ver_time:
            ticket_status_history.append({
                "id": f"tsh-today-{idx}-5", "ticket_id": t_id, "changed_by": "u-1", "from_status": "COMPLETED", "to_status": "VERIFIED", "created_at": admin_ver_time
            })

        # Spares used
        for sp_id, qty in item["spares_used"]:
            ticket_spares.append({
                "id": f"spt-today-{idx}-{sp_id}",
                "ticket_id": t_id,
                "spare_id": sp_id,
                "used_qty": qty,
                "used_qty_time": repair_start or raised_time,
                "logged_by_id": item["assigned_to_id"]
            })

        # Tools issued
        if item["tool_issued"]:
            tool_id, returned, duration_mins = item["tool_issued"]
            ticket_tools_data.append({
                "id": f"tlt-today-{idx}",
                "ticket_id": t_id,
                "tool_id": tool_id,
                "employee_id": item["assigned_to_id"],
                "taken_time": repair_start,
                "return_time": (repair_start + timedelta(minutes=duration_mins)) if returned and repair_start else None,
                "is_vacant": returned
            })

        # Media proofs
        for m_stage in item["media"]:
            ticket_media_data.append({
                "id": f"tm-today-{idx}-{m_stage}", "ticket_id": t_id,
                "media_url": f"https://storage.supabase.co/media/{item['ticket_no']}_{m_stage.lower()}.jpg",
                "media_type": "image/jpeg", "upload_stage": m_stage, "uploaded_by": item["assigned_to_id"],
                "file_name": f"{item['ticket_no']}_{m_stage.lower()}.jpg", "file_size": 245000
            })

    # B. HISTORICAL TICKETS (Days 1 to 30)
    titles_pool = [
        ("Steam Boiler Safety Valve Pressure Fluctuation", "Scale buildup on relief nozzle seat", "Steam / Boiler", "eq-1"),
        ("Walk-in Deep Freezer Temp Rising above -10°C", "Capillary tube frosting and condenser fan trip", "Refrigeration", "eq-2"),
        ("Dishwasher Wash Pump Cavitation & Low Pressure", "Foreign debris stuck in pump impeller housing", "Plumbing & RO", "eq-3"),
        ("Spiral Mixer Motor Noise & Belt Slip", "Motor drive belt loose and pulley misalignment", "Mechanical", "eq-4"),
        ("Induction Range Displaying Error Code E-04", "IGBT overheat sensor thermal resistance short", "Electrical", "eq-5"),
        ("Conveyor Fryer Temperature Controller Lockup", "PID controller thermocouple loose connection", "Electrical", "eq-6"),
        ("RO Water Plant High Permeate Conductivity (TDS)", "RO membrane fouling due to low anti-scalant dosing", "Plumbing & RO", "eq-7"),
        ("Boiler Feed Water Pump Mechanical Seal Drip", "Worn shaft packing seal after continuous run", "Steam / Boiler", "eq-1"),
        ("Cold Room Door Gasket Torn & Condensation", "Magnetic seal torn allowing ambient air leakage", "Refrigeration", "eq-2"),
        ("Dough Mixer Gearbox Oil Leakage", "Oil seal dried out causing transmission gear oil drip", "Mechanical", "eq-4"),
        ("Temporary Tabletop Griddle Thermostat Burnt", "Overheated contact points on non-asset unit", "Electrical", None) # custom equipment
    ]

    for i in range(1, 40):
        t_id = f"tck-hist-{i:03d}"
        days_ago = np.random.randint(1, 30)
        hours_ago = np.random.randint(1, 23)
        sample = titles_pool[i % len(titles_pool)]

        t_date = now - timedelta(days=days_ago, hours=hours_ago)
        t_no = f"TCK-{t_date.strftime('%Y%m%d')}-{100 + i}"

        bd_time = t_date - timedelta(minutes=np.random.randint(15, 60))
        raised_time = t_date
        
        # Delay: 15 to 90 mins
        response_delay_mins = np.random.randint(15, 90)
        repair_start = raised_time + timedelta(minutes=response_delay_mins)

        # MTTR: 45 mins to 240 mins
        mttr_mins = np.random.randint(45, 240)
        completion_time = repair_start + timedelta(minutes=mttr_mins)

        # Verification delays
        raiser_ver_delay = np.random.randint(15, 60)
        raiser_ver_time = completion_time + timedelta(minutes=raiser_ver_delay)

        admin_ver_delay = np.random.randint(30, 180)
        admin_ver_time = completion_time + timedelta(minutes=admin_ver_delay)

        st = "VERIFIED" if i % 4 != 0 else "COMPLETED"
        assigned_tech = np.random.choice(["u-2", "u-3", "u-4"])
        raiser_id = np.random.choice(["u-5", "u-6", "u-7", "u-8"])

        eq_id = sample[3]
        custom_eq = "Temporary Tabletop Griddle (Non-Asset)" if eq_id is None else None
        
        if eq_id:
            eq_record = next(e for e in equipments if e["id"] == eq_id)
            area_record = next(a for a in areas if a["id"] == eq_record["area_id"])
            zone_record = next(z for z in zones if z["id"] == area_record["zone_id"])
            kitchen_id = zone_record["kitchen_id"]
            area_id = area_record["id"]
        else:
            kitchen_id = "k-2"
            area_id = "a-4"

        ticket_data.append({
            "id": t_id,
            "ticket_no": t_no,
            "title": sample[0],
            "cause_of_issue": sample[1],
            "category": sample[2],
            "priority": np.random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"], p=[0.2, 0.4, 0.3, 0.1]),
            "status": st,
            "kitchen_id": kitchen_id,
            "area_id": area_id,
            "equipment_id": eq_id,
            "custom_equipment": custom_eq,
            "raised_by_id": raiser_id,
            "assigned_to_id": assigned_tech,
            "verified_by_id": "u-1" if st == "VERIFIED" else None,
            "breakdown_time": bd_time,
            "ticket_raised_time": raised_time,
            "repair_start_time": repair_start,
            "ticket_completion_time": completion_time,
            "updated_at": completion_time,
            "admin_verified": st == "VERIFIED",
            "admin_verified_at": admin_ver_time if st == "VERIFIED" else None,
            "raiser_verified": True,
            "raiser_verified_at": raiser_ver_time,
            "action_taken": f"Inspected fault on {sample[0]}, rectified failure point and restored operation.",
            "telegram_message_id": f"msg_tg_hist_{i}"
        })

        # History
        ticket_status_history.append({
            "id": f"tsh-hist-{i}-1", "ticket_id": t_id, "changed_by": raiser_id, "from_status": None, "to_status": "OPEN", "created_at": raised_time
        })
        ticket_status_history.append({
            "id": f"tsh-hist-{i}-2", "ticket_id": t_id, "changed_by": assigned_tech, "from_status": "OPEN", "to_status": "IN_PROGRESS", "created_at": repair_start
        })
        ticket_status_history.append({
            "id": f"tsh-hist-{i}-3", "ticket_id": t_id, "changed_by": assigned_tech, "from_status": "IN_PROGRESS", "to_status": "COMPLETED", "created_at": completion_time
        })
        if st == "VERIFIED":
            ticket_status_history.append({
                "id": f"tsh-hist-{i}-4", "ticket_id": t_id, "changed_by": "u-1", "from_status": "COMPLETED", "to_status": "VERIFIED", "created_at": admin_ver_time
            })

        # Spares
        if i % 2 == 0:
            sp_sample = spares[i % len(spares)]
            ticket_spares.append({
                "id": f"spt-hist-{i}",
                "ticket_id": t_id,
                "spare_id": sp_sample["id"],
                "used_qty": np.random.choice([1, 2, 3]),
                "used_qty_time": repair_start,
                "logged_by_id": assigned_tech
            })

        # Tools
        tool_sample = tools[i % len(tools)]
        ticket_tools_data.append({
            "id": f"tlt-hist-{i}",
            "ticket_id": t_id,
            "tool_id": tool_sample["id"],
            "employee_id": assigned_tech,
            "taken_time": repair_start,
            "return_time": completion_time,
            "is_vacant": True
        })

    # 8. PM Schedules & Overdue Flags (`rep_preventive_machine_schedule`)
    pm_schedules = []
    for eq in equipments:
        for m in range(1, 4):
            plan_d = (now - timedelta(days=m * 10)).date()
            # Simulate eq-2 (Cold Room) having an overdue PM to trigger Overdue PM correlation
            is_achieved = False if (eq["id"] == "eq-2" and m == 1) else np.random.choice([True, False], p=[0.85, 0.15])
            pm_schedules.append({
                "id": f"pm-{eq['id']}-{m}",
                "equipment_id": eq["id"],
                "plan_date": plan_d,
                "is_planned": True,
                "achieved_date": plan_d if is_achieved else None,
                "is_achieved": is_achieved,
                "frequency": "Monthly",
                "done_by": "u-2" if is_achieved else None,
                "remarks": "Overdue - parts delayed" if not is_achieved else "Standard 30-point preventive maintenance routine"
            })

    # 9. Daily Boiler & Electrical Logs
    boiler_logs = []
    electrical_logs = []
    for d in range(0, 31):
        log_date = (now - timedelta(days=d)).date()
        boiler_logs.append({
            "id": f"blr-log-{d}",
            "kitchen_id": "k-1",
            "log_date": log_date,
            "feed_water_ph": round(7.4 + np.random.uniform(-0.3, 0.3), 2),
            "feed_water_tds": round(120 + (180 if d in (0, 1, 4, 18) else np.random.uniform(-15, 30)), 1),
            "feed_water_hardness": round(5 + (18 if d in (0, 1, 4, 18) else np.random.uniform(-1, 2)), 1),
            "total_running_hours": 16.5,
            "steam_pressure_avg": 7.8,
            "status": True
        })
        electrical_logs.append({
            "id": f"elec-log-{d}",
            "kitchen_id": "k-1",
            "log_date": log_date,
            "daily_kwh_consumption": round(450 + np.random.uniform(-30, 80), 1),
            "ht_voltage_avg": round(415 + np.random.uniform(-10, 25), 1),
            "power_factor_avg": round(0.94 + np.random.uniform(-0.08, 0.04), 2),
            "status": True
        })

    return {
        "m_cluster": df_clusters,
        "m_kitchen": df_kitchens,
        "m_zone": df_zones,
        "m_area": df_areas,
        "m_user": df_users,
        "m_equipment": df_equipments,
        "m_spares": df_spares,
        "spare_tracker": df_spare_tracker,
        "m_tools": df_tools,
        "tickets": pd.DataFrame(ticket_data),
        "ticket_status_history": pd.DataFrame(ticket_status_history),
        "spare_ticket": pd.DataFrame(ticket_spares),
        "ticket_tools": pd.DataFrame(ticket_tools_data),
        "ticket_media": pd.DataFrame(ticket_media_data),
        "rep_preventive_machine_schedule": pd.DataFrame(pm_schedules),
        "daily_boiler_log": pd.DataFrame(boiler_logs),
        "daily_electrical_log": pd.DataFrame(electrical_logs)
    }
