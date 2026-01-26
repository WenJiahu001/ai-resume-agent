-- ============================================================
-- 用户表和会话表初始化脚本
-- 创建时间: 2026-01-23
-- 描述: 创建用户管理和会话管理所需的数据库表
-- ============================================================

-- 用户表：存储用户基本信息
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY COMMENT '用户唯一标识（UUID）',
    username VARCHAR(100) NOT NULL UNIQUE COMMENT '用户名，唯一',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 会话表：存储会话元数据（消息内容由 LangGraph checkpoint 管理）
CREATE TABLE IF NOT EXISTS threads (
    id VARCHAR(36) PRIMARY KEY COMMENT '会话唯一标识（UUID）',
    user_id VARCHAR(36) NOT NULL COMMENT '所属用户ID',
    title VARCHAR(255) COMMENT '会话标题（可从首条消息自动生成）',
    preview TEXT COMMENT '最后一条消息预览',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id) COMMENT '用户ID索引，加速按用户查询',
    INDEX idx_updated_at (updated_at) COMMENT '更新时间索引，加速排序查询'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话表';
