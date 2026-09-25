-- ==============================================================================
-- 1. RECREATE VIEW WITHOUT SECURITY INVOKER (Bypasses RLS for Dashboard)
-- ==============================================================================

CREATE OR REPLACE VIEW v_pmt_dashboard_tickets
WITH (security_invoker = false)
AS
SELECT 
    -- 1. Core Ticket Identification
    t.id AS id,
    t.ticket_no,
    t.title,
    t.category,
    t.priority,
    t.status,
    t.cause_of_issue,
    t.action_taken,
    t.telegram_message_id,

    -- 2. Location & Facility Hierarchy
    t.kitchen_id,
    k.name AS kitchen_name,
    k.cluster_id,
    cl.name AS cluster_name,
    t.area_id,
    a.area_name,
    a.zone_id,
    z.name AS zone_name,
    z.telegram_chat_id AS zone_telegram_chat_id,

    -- 3. Equipment & Asset Details (Standard, Testing, or Custom Non-Asset)
    te.equipment_id,
    te.testing_equipment_id,
    t.custom_equipment,
    COALESCE(NULLIF(TRIM(e.name), ''), NULLIF(TRIM(mte.name), ''), NULLIF(TRIM(t.custom_equipment), ''), 'Custom Asset / General') AS equipment_name,
    COALESCE(e.equipment_code, 'N/A') AS equipment_code,
    e.model AS equipment_model,
    CASE 
        WHEN e.id IS NOT NULL THEN 'Standard Registered Asset'
        WHEN mte.id IS NOT NULL THEN 'Testing Equipment'
        WHEN t.custom_equipment IS NOT NULL AND TRIM(t.custom_equipment) != '' THEN 'Custom Equipment'
        ELSE 'General Asset'
    END AS asset_type,
    (t.custom_equipment IS NOT NULL AND TRIM(t.custom_equipment) != '') AS is_custom_equipment,

    -- 4. People & Roles Involved
    t.raised_by_id,
    u_raiser.name AS raised_by_name,
    u_raiser.amp_id AS raiser_emp_id,
    t.assigned_to_id,
    COALESCE(u_tech.name, '⏳ Unassigned') AS technician_name,
    u_tech.amp_id AS technician_emp_id,
    u_tech.department AS technician_department,
    t.verified_by_id,
    u_admin.name AS admin_verifier_name,

    -- 5. Timestamps
    t.breakdown_time,
    t.ticket_raised_time,
    t.assigned_to_time,
    t.repair_start_time,
    t.ticket_completion_time,
    t.updated_at,
    t.raiser_verified_at,
    t.admin_verified_at,
    DATE(t.ticket_raised_time) AS ticket_raised_date,
    (DATE(t.ticket_raised_time) = CURRENT_DATE) AS is_today,

    -- 6. Calculated SLA Latencies & Durations (Pre-computed)
    -- Response Delay (Mins from Raised to Work Started)
    ROUND((EXTRACT(EPOCH FROM (COALESCE(t.repair_start_time, NOW()) - t.ticket_raised_time)) / 60)::numeric, 1) AS response_delay_mins,
    
    -- Response Delay Formatted
    CASE 
        WHEN t.repair_start_time IS NOT NULL THEN 
            ROUND((EXTRACT(EPOCH FROM (t.repair_start_time - t.ticket_raised_time)) / 60)::numeric, 0) || ' mins'
        ELSE 
            'Waiting (' || ROUND((EXTRACT(EPOCH FROM (NOW() - t.ticket_raised_time)) / 60)::numeric, 0) || 'm)'
    END AS response_delay_display,
    
    -- MTTR / Hands-on Repair Time (Mins & Hours)
    ROUND((EXTRACT(EPOCH FROM (t.ticket_completion_time - t.repair_start_time)) / 60)::numeric, 1) AS mttr_mins,
    ROUND((EXTRACT(EPOCH FROM (t.ticket_completion_time - t.repair_start_time)) / 3600)::numeric, 2) AS mttr_hours,
    CASE 
        WHEN t.ticket_completion_time IS NOT NULL THEN 
            ROUND((EXTRACT(EPOCH FROM (t.ticket_completion_time - t.repair_start_time)) / 60)::numeric, 0) || ' mins'
        WHEN t.repair_start_time IS NOT NULL THEN 
            'In Progress (' || ROUND((EXTRACT(EPOCH FROM (NOW() - t.repair_start_time)) / 60)::numeric, 0) || 'm)'
        ELSE '—'
    END AS repair_duration_display,

    -- Total Machine Downtime (Hours)
    ROUND((EXTRACT(EPOCH FROM (COALESCE(t.ticket_completion_time, NOW()) - t.breakdown_time)) / 3600)::numeric, 2) AS total_downtime_hours,

    -- Verification Delays (Mins)
    ROUND((EXTRACT(EPOCH FROM (t.raiser_verified_at - t.ticket_completion_time)) / 60)::numeric, 1) AS raiser_ver_delay_mins,
    ROUND((EXTRACT(EPOCH FROM (t.admin_verified_at - t.ticket_completion_time)) / 60)::numeric, 1) AS admin_ver_delay_mins,

    -- 7. Governance & Verification Flags
    COALESCE(t.raiser_verified, FALSE) AS is_raiser_verified,
    COALESCE(t.admin_verified, FALSE) AS is_admin_verified,
    (COALESCE(t.raiser_verified, FALSE) = TRUE AND COALESCE(t.admin_verified, FALSE) = TRUE) AS is_dual_verified,

    -- 8. Sub-Aggregated Spares Used (Count & JSON Array)
    COALESCE((SELECT SUM(st.used_qty) FROM spare_ticket st WHERE st.ticket_id = t.id), 0) AS total_spares_used_count,
    COALESCE((
        SELECT json_agg(json_build_object(
            'spare_code', s.spare_code,
            'spare_name', s.spare_name,
            'used_qty', st.used_qty,
            'uom', s.uom,
            'is_critical', s.is_critical
        ))
        FROM spare_ticket st
        JOIN m_spares s ON st.spare_id = s.id
        WHERE st.ticket_id = t.id
    ), '[]'::json) AS spares_json,

    -- 9. Sub-Aggregated Tools Issued (Active Held Count & JSON Array)
    COALESCE((SELECT COUNT(*) FROM ticket_tools tt WHERE tt.ticket_id = t.id AND (tt.return_time IS NULL OR tt.is_vacant = FALSE)), 0) AS active_tools_held_count,
    COALESCE((
        SELECT json_agg(json_build_object(
            'tool_name', tl.tool_name,
            'taken_time', tt.taken_time,
            'return_time', tt.return_time,
            'is_vacant', tt.is_vacant
        ))
        FROM ticket_tools tt
        JOIN m_tools tl ON tt.tool_id = tl.id
        WHERE tt.ticket_id = t.id
    ), '[]'::json) AS tools_json,

    -- 10. Sub-Aggregated Media Proofs (Count & JSON Array)
    COALESCE((SELECT COUNT(*) FROM ticket_media tm WHERE tm.ticket_id = t.id), 0) AS media_proofs_count,
    COALESCE((
        SELECT json_agg(json_build_object(
            'media_url', tm.media_url,
            'upload_stage', tm.upload_stage,
            'file_name', tm.file_name,
            'file_size_kb', ROUND((tm.file_size / 1024.0)::numeric, 1)
        ))
        FROM ticket_media tm
        WHERE tm.ticket_id = t.id
    ), '[]'::json) AS media_json,

    -- 11. Status Lifecycle Timeline (JSON Array)
    COALESCE((
        SELECT json_agg(json_build_object(
            'from_status', tsh.from_status,
            'to_status', tsh.to_status,
            'created_at', tsh.created_at,
            'changed_by', tsh.changed_by
        ) ORDER BY tsh.created_at ASC)
        FROM ticket_status_history tsh
        WHERE tsh.ticket_id = t.id
    ), '[]'::json) AS status_history_json

FROM tickets t
LEFT JOIN m_kitchen k ON t.kitchen_id = k.id
LEFT JOIN m_cluster cl ON k.cluster_id = cl.id
LEFT JOIN m_area a ON t.area_id = a.id
LEFT JOIN m_zone z ON a.zone_id = z.id
LEFT JOIN ticket_equipments te ON te.ticket_id = t.id
LEFT JOIN m_equipment e ON te.equipment_id = e.id
LEFT JOIN m_testing_equipment mte ON te.testing_equipment_id = mte.id
LEFT JOIN m_user u_raiser ON t.raised_by_id = u_raiser.id
LEFT JOIN m_user u_tech ON t.assigned_to_id = u_tech.id
LEFT JOIN m_user u_admin ON t.verified_by_id = u_admin.id;

-- Grant permissions to view
GRANT SELECT ON v_pmt_dashboard_tickets TO authenticated;
GRANT SELECT ON v_pmt_dashboard_tickets TO anon;
GRANT SELECT ON v_pmt_dashboard_tickets TO service_role;
