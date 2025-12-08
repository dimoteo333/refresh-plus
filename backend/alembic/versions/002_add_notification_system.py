"""add notification system

Revision ID: 002
Revises: 001
Create Date: 2024-12-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # 1. User 테이블에 알림 관련 필드 추가
    op.add_column('users', sa.Column('fcm_token', sa.String(512), nullable=True))
    op.add_column('users', sa.Column('web_push_subscription', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('preferred_notification_channel', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('notification_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('device_type', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('ios_version', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('pwa_installed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('successful_bookings', sa.Integer(), nullable=False, server_default='0'))

    # 2. notification_types 테이블 생성
    op.create_table(
        'notification_types',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_title', sa.String(255), nullable=True),
        sa.Column('template_body', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. notification_preferences 테이블 생성
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('notification_type_id', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['notification_type_id'], ['notification_types.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'notification_type_id', name='uq_user_notif_type')
    )
    op.create_index('idx_notif_prefs_user', 'notification_preferences', ['user_id'])
    op.create_index('idx_notif_prefs_type', 'notification_preferences', ['notification_type_id'])

    # 4. notification_logs 테이블 생성
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('notification_type_id', sa.String(), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('dedup_key', sa.String(255), nullable=True),
        sa.Column('dedup_expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['notification_type_id'], ['notification_types.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_notif_logs_user', 'notification_logs', ['user_id'])
    op.create_index('idx_notif_logs_type', 'notification_logs', ['notification_type_id'])
    op.create_index('idx_notif_logs_status', 'notification_logs', ['status'])
    op.create_index('idx_notif_logs_dedup', 'notification_logs', ['dedup_key', 'dedup_expires_at'])
    op.create_index('idx_notif_logs_created', 'notification_logs', ['created_at'], postgresql_using='btree')

    # 5. 초기 notification_types 데이터 시딩
    op.execute("""
        INSERT INTO notification_types (id, name, description, template_title, template_body, enabled)
        VALUES
        (
            'wishlist_available',
            '위시리스트 예약 가능',
            '찜한 숙소가 예약 가능 상태가 되었을 때',
            '예약 가능 알림',
            '찜해둔 ''{accommodation_name}'' {date}에 예약 가능합니다. 지금 바로 신청하세요!',
            true
        ),
        (
            'high_win_probability',
            '당첨 가능성 높음',
            '사용자 점수가 평균 당첨 점수보다 높을 때',
            '당첨 확률 높음!',
            '''{accommodation_name}'' {date}에 신청하면 당첨 가능성이 높습니다! (내 점수: {user_score}점, 평균: {avg_score}점)',
            true
        )
    """)


def downgrade():
    # 역순으로 롤백
    # 1. notification_logs 테이블 삭제
    op.drop_index('idx_notif_logs_created', 'notification_logs')
    op.drop_index('idx_notif_logs_dedup', 'notification_logs')
    op.drop_index('idx_notif_logs_status', 'notification_logs')
    op.drop_index('idx_notif_logs_type', 'notification_logs')
    op.drop_index('idx_notif_logs_user', 'notification_logs')
    op.drop_table('notification_logs')

    # 2. notification_preferences 테이블 삭제
    op.drop_index('idx_notif_prefs_type', 'notification_preferences')
    op.drop_index('idx_notif_prefs_user', 'notification_preferences')
    op.drop_table('notification_preferences')

    # 3. notification_types 테이블 삭제
    op.drop_table('notification_types')

    # 4. User 테이블에서 알림 관련 필드 제거
    op.drop_column('users', 'successful_bookings')
    op.drop_column('users', 'pwa_installed')
    op.drop_column('users', 'ios_version')
    op.drop_column('users', 'device_type')
    op.drop_column('users', 'notification_enabled')
    op.drop_column('users', 'preferred_notification_channel')
    op.drop_column('users', 'web_push_subscription')
    op.drop_column('users', 'fcm_token')
