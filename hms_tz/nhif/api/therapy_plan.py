import frappe

def before_insert(doc):
    total_sessions = 0
    for entry in doc.therapy_plan_details:
        if entry.no_of_sessions:
            total_sessions += entry.no_of_sessions
    doc.total_sessions =  total_sessions

def validate(doc, method):
    set_totals(doc)
    set_status(doc)

def set_status(doc):
    if (
        not doc.total_sessions_completed and 
        not doc.total_sessions
    ):
        doc.status = 'Not Serviced'
    
    if (
        doc.total_sessions and 
        not doc.total_sessions_completed
    ):
        doc.status = 'Not Started'

    else:
        if doc.total_sessions_completed < doc.total_sessions:
            doc.status = 'In Progress'

        elif (
            doc.total_sessions != 0 and 
            (doc.total_sessions_completed == doc.total_sessions)
        ):
            doc.status = 'Completed'

def set_totals(doc):
    total_sessions_completed = 0
    for entry in doc.therapy_plan_details:
        if entry.sessions_completed:
            total_sessions_completed += entry.sessions_completed

    doc.db_set('total_sessions_completed', total_sessions_completed)
