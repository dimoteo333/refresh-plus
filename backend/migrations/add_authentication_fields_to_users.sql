-- users 테이블에 인증 관련 컬럼 추가
-- 로그인 시스템 구현을 위한 마이그레이션

-- 인증 관련 컬럼
ALTER TABLE users ADD COLUMN IF NOT EXISTS lulu_lala_user_id VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS encrypted_password BYTEA;
ALTER TABLE users ADD COLUMN IF NOT EXISTS encryption_key_version INTEGER DEFAULT 1;

-- 세션 관리 컬럼
ALTER TABLE users ADD COLUMN IF NOT EXISTS session_cookies JSON;
ALTER TABLE users ADD COLUMN IF NOT EXISTS session_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;

-- 보안 컬럼
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

-- 리프레시 토큰 컬럼
ALTER TABLE users ADD COLUMN IF NOT EXISTS refresh_token_jti VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS refresh_token_expires_at TIMESTAMP;

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS ix_users_lulu_lala_user_id ON users(lulu_lala_user_id);
CREATE INDEX IF NOT EXISTS ix_users_refresh_token_jti ON users(refresh_token_jti);
CREATE INDEX IF NOT EXISTS ix_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS ix_users_is_verified ON users(is_verified);
CREATE INDEX IF NOT EXISTS ix_users_session_expires_at ON users(session_expires_at);
CREATE INDEX IF NOT EXISTS ix_users_locked_until ON users(locked_until);

-- 기존 사용자에 대한 기본값 설정
UPDATE users
SET
    is_active = TRUE,
    is_verified = FALSE,
    failed_login_attempts = 0,
    encryption_key_version = 1
WHERE is_active IS NULL;
