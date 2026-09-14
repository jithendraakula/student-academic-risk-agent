from alembic import op
import sqlalchemy as sa

revision='0001_student_cases'
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind(); insp=sa.inspect(bind); tables=set(insp.get_table_names())
    if 'student_cases' not in tables:
        op.create_table('student_cases',
            sa.Column('id',sa.String(40),primary_key=True),sa.Column('student_id',sa.String(32),nullable=False),
            sa.Column('status',sa.String(16),nullable=False,server_default='OPEN'),sa.Column('opened_at',sa.DateTime(),nullable=False),
            sa.Column('updated_at',sa.DateTime(),nullable=False),sa.Column('completed_at',sa.DateTime()),sa.Column('completed_by',sa.String(32)),
            sa.Column('completion_category',sa.String(64)),sa.Column('completion_reason',sa.String(255)),sa.Column('completion_notes',sa.Text()),
            sa.Column('follow_up_outcome',sa.String(128)),sa.Column('completion_metadata',sa.JSON(),nullable=False),sa.Column('last_risk_snapshot_at',sa.DateTime()),
            sa.ForeignKeyConstraint(['student_id'],['students.id']),sa.ForeignKeyConstraint(['completed_by'],['users.id']))
        op.create_index('ix_student_cases_student_id','student_cases',['student_id'])
        op.create_index('ix_student_cases_status','student_cases',['status'])
        op.create_index('ix_student_cases_updated_at','student_cases',['updated_at'])
    if 'case_events' not in tables:
        op.create_table('case_events',sa.Column('id',sa.String(40),primary_key=True),sa.Column('case_id',sa.String(40),nullable=False),sa.Column('student_id',sa.String(32),nullable=False),sa.Column('actor_id',sa.String(32)),sa.Column('event_type',sa.String(64),nullable=False),sa.Column('from_status',sa.String(16)),sa.Column('to_status',sa.String(16)),sa.Column('notes',sa.Text()),sa.Column('metadata',sa.JSON(),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False),sa.ForeignKeyConstraint(['case_id'],['student_cases.id']),sa.ForeignKeyConstraint(['student_id'],['students.id']),sa.ForeignKeyConstraint(['actor_id'],['users.id']))
        op.create_index('ix_case_events_case_id','case_events',['case_id']); op.create_index('ix_case_events_student_id','case_events',['student_id']); op.create_index('ix_case_events_event_type','case_events',['event_type']); op.create_index('ix_case_events_created_at','case_events',['created_at'])
    if 'alerts_interventions' in tables:
        cols={c['name'] for c in insp.get_columns('alerts_interventions')}
        if 'case_id' not in cols:
            op.add_column('alerts_interventions',sa.Column('case_id',sa.String(40),nullable=True)); op.create_index('ix_alerts_interventions_case_id','alerts_interventions',['case_id']); op.create_foreign_key('fk_alerts_interventions_case','alerts_interventions','student_cases',['case_id'],['id'])
    if 'uq_student_cases_active_student' not in {i['name'] for i in insp.get_indexes('student_cases')}:
        op.create_index('uq_student_cases_active_student','student_cases',['student_id'],unique=True,sqlite_where=sa.text("status = 'OPEN'"))

def downgrade():
    bind=op.get_bind(); insp=sa.inspect(bind); tables=set(insp.get_table_names())
    if 'alerts_interventions' in tables and 'case_id' in {c['name'] for c in insp.get_columns('alerts_interventions')}:
        try: op.drop_constraint('fk_alerts_interventions_case','alerts_interventions',type_='foreignkey')
        except Exception: pass
        try: op.drop_index('ix_alerts_interventions_case_id','alerts_interventions')
        except Exception: pass
        op.drop_column('alerts_interventions','case_id')
    if 'case_events' in tables: op.drop_table('case_events')
    if 'student_cases' in tables: op.drop_table('student_cases')
