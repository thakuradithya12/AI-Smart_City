from django.db import migrations


FORWARD_SQL = ["""
CREATE OR REPLACE FUNCTION reject_append_only_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION '% is append-only; UPDATE and DELETE are forbidden', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;
""", """
CREATE TRIGGER complaints_statusevent_append_only
BEFORE UPDATE OR DELETE ON complaints_statusevent
FOR EACH ROW EXECUTE FUNCTION reject_append_only_mutation();
""", """
CREATE TRIGGER audit_auditevent_append_only
BEFORE UPDATE OR DELETE ON audit_auditevent
FOR EACH ROW EXECUTE FUNCTION reject_append_only_mutation();
"""]

REVERSE_SQL = ["""
DROP TRIGGER IF EXISTS complaints_statusevent_append_only ON complaints_statusevent;
""", """
DROP TRIGGER IF EXISTS audit_auditevent_append_only ON audit_auditevent;
""", """
DROP FUNCTION IF EXISTS reject_append_only_mutation();
"""]


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0001_initial"),
        ("complaints", "0002_gps_accuracy_decimal"),
    ]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
