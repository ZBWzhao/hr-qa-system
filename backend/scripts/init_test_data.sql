-- =====================================================
-- HR Copilot 测试数据初始化脚本
-- =====================================================
-- 功能：
-- 1. 为每个部门创建至少3个用户（每个部门最多1个HR）
-- 2. 为每个用户创建2-3种不同类型的工单
-- 3. 创建公告和公告已读记录
-- 4. 创建问答记录和反馈
-- 5. 确保所有数据之间的关联性
--
-- 使用方法：
-- mysql -u root -p hr_copilot < init_test_data.sql
-- =====================================================

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 清空现有数据（可选，谨慎使用）
-- TRUNCATE TABLE biz_comment;
-- TRUNCATE TABLE biz_ticket;
-- TRUNCATE TABLE qa_feedback;
-- TRUNCATE TABLE qa_record;
-- TRUNCATE TABLE qa_miss;
-- TRUNCATE TABLE sys_notice_read;
-- TRUNCATE TABLE sys_notice;
-- TRUNCATE TABLE sys_user;
-- TRUNCATE TABLE sys_department;

-- =====================================================
-- 1. 创建部门
-- =====================================================

-- 检查并创建部门
INSERT INTO sys_department (name, parent_id, sort_order, created_at)
SELECT '人力资源部', NULL, 1, NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_department WHERE name = '人力资源部');

INSERT INTO sys_department (name, parent_id, sort_order, created_at)
SELECT '技术部', NULL, 2, NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_department WHERE name = '技术部');

INSERT INTO sys_department (name, parent_id, sort_order, created_at)
SELECT '市场部', NULL, 3, NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_department WHERE name = '市场部');

INSERT INTO sys_department (name, parent_id, sort_order, created_at)
SELECT '财务部', NULL, 4, NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_department WHERE name = '财务部');

INSERT INTO sys_department (name, parent_id, sort_order, created_at)
SELECT '行政部', NULL, 5, NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_department WHERE name = '行政部');

-- 获取部门ID（用于后续插入）
SET @dept_hr = (SELECT id FROM sys_department WHERE name = '人力资源部' LIMIT 1);
SET @dept_tech = (SELECT id FROM sys_department WHERE name = '技术部' LIMIT 1);
SET @dept_market = (SELECT id FROM sys_department WHERE name = '市场部' LIMIT 1);
SET @dept_finance = (SELECT id FROM sys_department WHERE name = '财务部' LIMIT 1);
SET @dept_admin = (SELECT id FROM sys_department WHERE name = '行政部' LIMIT 1);

-- =====================================================
-- 2. 创建用户
-- =====================================================
-- 密码: 123456
-- 密码哈希: $2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6

-- 人力资源部用户（1个HR + 2个员工 = 3人）
INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'zhangsan', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '张三', 'zhangsan@company.com', @dept_hr, 'hr', 1, DATE_SUB(NOW(), INTERVAL 2 YEAR), DATE_ADD(NOW(), INTERVAL 1 YEAR), DATE_SUB(NOW(), INTERVAL 18 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'zhangsan');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'lisi', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '李四', 'lisi@company.com', @dept_hr, 'employee', 1, DATE_SUB(NOW(), INTERVAL 18 MONTH), DATE_ADD(NOW(), INTERVAL 18 MONTH), DATE_SUB(NOW(), INTERVAL 12 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'lisi');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'wangwu', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '王五', 'wangwu@company.com', @dept_hr, 'employee', 1, DATE_SUB(NOW(), INTERVAL 1 YEAR), DATE_ADD(NOW(), INTERVAL 2 YEAR), DATE_SUB(NOW(), INTERVAL 6 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'wangwu');

-- 技术部用户（1个HR + 5个员工 = 6人）
INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'liudehua', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '刘德华', 'liudehua@company.com', @dept_tech, 'hr', 1, DATE_SUB(NOW(), INTERVAL 3 YEAR), DATE_ADD(NOW(), INTERVAL 1 YEAR), DATE_SUB(NOW(), INTERVAL 30 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'liudehua');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'zhangxueyou', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '张学友', 'zhangxueyou@company.com', @dept_tech, 'employee', 1, DATE_SUB(NOW(), INTERVAL 2 YEAR), DATE_ADD(NOW(), INTERVAL 1 YEAR), DATE_SUB(NOW(), INTERVAL 18 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'zhangxueyou');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'guofucheng', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '郭富城', 'guofucheng@company.com', @dept_tech, 'employee', 1, DATE_SUB(NOW(), INTERVAL 15 MONTH), DATE_ADD(NOW(), INTERVAL 18 MONTH), DATE_SUB(NOW(), INTERVAL 9 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'guofucheng');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'liming', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '黎明', 'liming@company.com', @dept_tech, 'employee', 1, DATE_SUB(NOW(), INTERVAL 1 YEAR), DATE_ADD(NOW(), INTERVAL 2 YEAR), DATE_SUB(NOW(), INTERVAL 6 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'liming');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'zhoujielun', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '周杰伦', 'zhoujielun@company.com', @dept_tech, 'employee', 1, DATE_SUB(NOW(), INTERVAL 8 MONTH), DATE_ADD(NOW(), INTERVAL 2 YEAR), DATE_SUB(NOW(), INTERVAL 2 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'zhoujielun');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'linjunjie', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '林俊杰', 'linjunjie@company.com', @dept_tech, 'employee', 1, DATE_SUB(NOW(), INTERVAL 6 MONTH), DATE_ADD(NOW(), INTERVAL 2 YEAR), DATE_ADD(NOW(), INTERVAL 1 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'linjunjie');

-- 市场部用户（1个HR + 4个员工 = 5人）
INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'chenglong', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '成龙', 'chenglong@company.com', @dept_market, 'hr', 1, DATE_SUB(NOW(), INTERVAL 2 YEAR), DATE_ADD(NOW(), INTERVAL 1 YEAR), DATE_SUB(NOW(), INTERVAL 18 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'chenglong');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'lianjie', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '李连杰', 'lianjie@company.com', @dept_market, 'employee', 1, DATE_SUB(NOW(), INTERVAL 18 MONTH), DATE_ADD(NOW(), INTERVAL 18 MONTH), DATE_SUB(NOW(), INTERVAL 12 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'lianjie');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'zhenzidan', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '甄子丹', 'zhenzidan@company.com', @dept_market, 'employee', 1, DATE_SUB(NOW(), INTERVAL 1 YEAR), DATE_ADD(NOW(), INTERVAL 2 YEAR), DATE_SUB(NOW(), INTERVAL 6 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'zhenzidan');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'wuyanzu', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '吴彦祖', 'wuyanzu@company.com', @dept_market, 'employee', 1, DATE_SUB(NOW(), INTERVAL 10 MONTH), DATE_ADD(NOW(), INTERVAL 2 YEAR), DATE_SUB(NOW(), INTERVAL 4 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'wuyanzu');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'pengyuyan', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '彭于晏', 'pengyuyan@company.com', @dept_market, 'employee', 1, DATE_SUB(NOW(), INTERVAL 5 MONTH), DATE_ADD(NOW(), INTERVAL 2 YEAR), DATE_ADD(NOW(), INTERVAL 2 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'pengyuyan');

-- 财务部用户（1个HR + 3个员工 = 4人）
INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'yangmi', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '杨幂', 'yangmi@company.com', @dept_finance, 'hr', 1, DATE_SUB(NOW(), INTERVAL 2 YEAR), DATE_ADD(NOW(), INTERVAL 1 YEAR), DATE_SUB(NOW(), INTERVAL 18 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'yangmi');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'zhaoliying', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '赵丽颖', 'zhaoliying@company.com', @dept_finance, 'employee', 1, DATE_SUB(NOW(), INTERVAL 15 MONTH), DATE_ADD(NOW(), INTERVAL 18 MONTH), DATE_SUB(NOW(), INTERVAL 9 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'zhaoliying');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'tangyan', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '唐嫣', 'tangyan@company.com', @dept_finance, 'employee', 1, DATE_SUB(NOW(), INTERVAL 1 YEAR), DATE_ADD(NOW(), INTERVAL 2 YEAR), DATE_SUB(NOW(), INTERVAL 6 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'tangyan');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'liushishi', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '刘诗诗', 'liushishi@company.com', @dept_finance, 'employee', 1, DATE_SUB(NOW(), INTERVAL 8 MONTH), DATE_ADD(NOW(), INTERVAL 2 YEAR), DATE_SUB(NOW(), INTERVAL 2 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'liushishi');

-- 行政部用户（1个HR + 3个员工 = 4人）
INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'huangbo', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '黄渤', 'huangbo@company.com', @dept_admin, 'hr', 1, DATE_SUB(NOW(), INTERVAL 3 YEAR), DATE_ADD(NOW(), INTERVAL 1 YEAR), DATE_SUB(NOW(), INTERVAL 30 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'huangbo');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'xuzheng', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '徐峥', 'xuzheng@company.com', @dept_admin, 'employee', 1, DATE_SUB(NOW(), INTERVAL 2 YEAR), DATE_ADD(NOW(), INTERVAL 1 YEAR), DATE_SUB(NOW(), INTERVAL 18 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'xuzheng');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'wangbaoqiang', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '王宝强', 'wangbaoqiang@company.com', @dept_admin, 'employee', 1, DATE_SUB(NOW(), INTERVAL 18 MONTH), DATE_ADD(NOW(), INTERVAL 18 MONTH), DATE_SUB(NOW(), INTERVAL 12 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'wangbaoqiang');

INSERT INTO sys_user (username, password_hash, real_name, email, department_id, role, status, hire_date, contract_end_date, probation_end_date, created_at, updated_at)
SELECT 'dengchao', '$2b$12$i/8OuNvEeDmHwXymFFoVpOTS/AohV9wnHR0BZ4.A4kkNCReQOSoN6', '邓超', 'dengchao@company.com', @dept_admin, 'employee', 1, DATE_SUB(NOW(), INTERVAL 1 YEAR), DATE_ADD(NOW(), INTERVAL 2 YEAR), DATE_SUB(NOW(), INTERVAL 6 MONTH), NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE username = 'dengchao');

-- =====================================================
-- 3. 创建工单
-- =====================================================

-- 为每个用户创建2-3种不同类型的工单

-- 张三（人力资源部HR）的工单
SET @user_zhangsan = (SELECT id FROM sys_user WHERE username = 'zhangsan' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050001', '请假申请', '年假申请', '申请年假，需要回家处理个人事务', 'completed', @user_zhangsan, NULL, '已批准', DATE_SUB(NOW(), INTERVAL 2 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050001');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050002', '证明开具', '在职证明申请', '需要开具在职证明用于办理签证', 'pending', @user_zhangsan, NULL, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050002');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050003', '信息变更', '手机号码变更', '更换了新的手机号码', 'completed', @user_zhangsan, NULL, '已更新系统信息', DATE_SUB(NOW(), INTERVAL 1 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050003');

-- 李四（人力资源部员工）的工单
SET @user_lisi = (SELECT id FROM sys_user WHERE username = 'lisi' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050004', '考勤异常', '忘打卡申请', '早上忘记打卡', 'pending', @user_lisi, @user_zhangsan, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050004');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050005', '报销薪资', '差旅费报销', '出差期间产生的差旅费用', 'completed', @user_lisi, @user_zhangsan, '已审批通过', DATE_SUB(NOW(), INTERVAL 3 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 7 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050005');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050006', '其他', 'IT设备申请', '申请新的笔记本电脑', 'pending', @user_lisi, @user_zhangsan, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050006');

-- 王五（人力资源部员工）的工单
SET @user_wangwu = (SELECT id FROM sys_user WHERE username = 'wangwu' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050007', '请假申请', '病假申请', '身体不适，需要休息', 'completed', @user_wangwu, @user_zhangsan, '已批准', DATE_SUB(NOW(), INTERVAL 5 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 6 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050007');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050008', '证明开具', '收入证明申请', '需要开具收入证明用于办理贷款', 'pending', @user_wangwu, @user_zhangsan, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050008');

-- 刘德华（技术部HR）的工单
SET @user_liudehua = (SELECT id FROM sys_user WHERE username = 'liudehua' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050009', '请假申请', '事假申请', '家中有事需要处理', 'pending', @user_liudehua, NULL, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050009');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050010', '信息变更', '银行卡号变更', '更换工资卡', 'completed', @user_liudehua, NULL, '已更新系统信息', DATE_SUB(NOW(), INTERVAL 2 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050010');

-- 张学友（技术部员工）的工单
SET @user_zhangxueyou = (SELECT id FROM sys_user WHERE username = 'zhangxueyou' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050011', '考勤异常', '迟到说明', '今天迟到需要说明原因', 'pending', @user_zhangxueyou, @user_liudehua, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050011');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050012', '报销薪资', '办公用品报销', '购买办公用品费用', 'completed', @user_zhangxueyou, @user_liudehua, '已审批通过', DATE_SUB(NOW(), INTERVAL 4 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 6 DAY), DATE_SUB(NOW(), INTERVAL 4 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050012');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050013', '其他', '会议室预定', '需要预定会议室', 'pending', @user_zhangxueyou, @user_liudehua, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050013');

-- 郭富城（技术部员工）的工单
SET @user_guofucheng = (SELECT id FROM sys_user WHERE username = 'guofucheng' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050014', '请假申请', '年假申请', '申请年假休息', 'completed', @user_guofucheng, @user_liudehua, '已批准', DATE_SUB(NOW(), INTERVAL 3 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 7 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050014');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050015', '证明开具', '在职证明申请', '需要开具在职证明', 'pending', @user_guofucheng, @user_liudehua, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050015');

-- 黎明（技术部员工）的工单
SET @user_liming = (SELECT id FROM sys_user WHERE username = 'liming' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050016', '信息变更', '手机号码变更', '更换了新的手机号码', 'completed', @user_liming, @user_liudehua, '已更新系统信息', DATE_SUB(NOW(), INTERVAL 2 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050016');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050017', '考勤异常', '忘打卡申请', '早上忘记打卡', 'pending', @user_liming, @user_liudehua, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050017');

-- 周杰伦（技术部员工）的工单
SET @user_zhoujielun = (SELECT id FROM sys_user WHERE username = 'zhoujielun' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050018', '报销薪资', '差旅费报销', '出差期间产生的差旅费用', 'pending', @user_zhoujielun, @user_liudehua, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050018');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050019', '请假申请', '事假申请', '家中有急事', 'completed', @user_zhoujielun, @user_liudehua, '已批准', DATE_SUB(NOW(), INTERVAL 1 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050019');

-- 林俊杰（技术部员工）的工单
SET @user_linjunjie = (SELECT id FROM sys_user WHERE username = 'linjunjie' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050020', '其他', 'IT设备申请', '申请新的显示器', 'pending', @user_linjunjie, @user_liudehua, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050020');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050021', '证明开具', '收入证明申请', '需要开具收入证明', 'pending', @user_linjunjie, @user_liudehua, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050021');

-- 成龙（市场部HR）的工单
SET @user_chenglong = (SELECT id FROM sys_user WHERE username = 'chenglong' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050022', '请假申请', '年假申请', '申请年假', 'completed', @user_chenglong, NULL, '已批准', DATE_SUB(NOW(), INTERVAL 2 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050022');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050023', '信息变更', '银行卡号变更', '更换工资卡', 'pending', @user_chenglong, NULL, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050023');

-- 李连杰（市场部员工）的工单
SET @user_lianjie = (SELECT id FROM sys_user WHERE username = 'lianjie' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050024', '考勤异常', '迟到说明', '地铁故障导致迟到', 'pending', @user_lianjie, @user_chenglong, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050024');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050025', '报销薪资', '差旅费报销', '出差费用报销', 'completed', @user_lianjie, @user_chenglong, '已审批通过', DATE_SUB(NOW(), INTERVAL 3 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 6 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050025');

-- 甄子丹（市场部员工）的工单
SET @user_zhenzidan = (SELECT id FROM sys_user WHERE username = 'zhenzidan' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050026', '请假申请', '病假申请', '身体不适', 'completed', @user_zhenzidan, @user_chenglong, '已批准', DATE_SUB(NOW(), INTERVAL 4 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 4 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050026');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050027', '证明开具', '在职证明申请', '需要开具在职证明', 'pending', @user_zhenzidan, @user_chenglong, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050027');

-- 吴彦祖（市场部员工）的工单
SET @user_wuyanzu = (SELECT id FROM sys_user WHERE username = 'wuyanzu' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050028', '其他', '会议室预定', '需要预定会议室', 'pending', @user_wuyanzu, @user_chenglong, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050028');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050029', '信息变更', '手机号码变更', '更换手机号码', 'completed', @user_wuyanzu, @user_chenglong, '已更新系统信息', DATE_SUB(NOW(), INTERVAL 2 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050029');

-- 彭于晏（市场部员工）的工单
SET @user_pengyuyan = (SELECT id FROM sys_user WHERE username = 'pengyuyan' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050030', '考勤异常', '忘打卡申请', '早上忘记打卡', 'pending', @user_pengyuyan, @user_chenglong, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050030');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050031', '请假申请', '事假申请', '需要处理私事', 'completed', @user_pengyuyan, @user_chenglong, '已批准', DATE_SUB(NOW(), INTERVAL 3 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050031');

-- 杨幂（财务部HR）的工单
SET @user_yangmi = (SELECT id FROM sys_user WHERE username = 'yangmi' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050032', '请假申请', '年假申请', '申请年假', 'pending', @user_yangmi, NULL, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050032');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050033', '证明开具', '收入证明申请', '需要开具收入证明', 'completed', @user_yangmi, NULL, '已开具', DATE_SUB(NOW(), INTERVAL 2 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050033');

-- 赵丽颖（财务部员工）的工单
SET @user_zhaoliying = (SELECT id FROM sys_user WHERE username = 'zhaoliying' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050034', '报销薪资', '差旅费报销', '出差费用报销', 'pending', @user_zhaoliying, @user_yangmi, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050034');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050035', '信息变更', '银行卡号变更', '更换工资卡', 'completed', @user_zhaoliying, @user_yangmi, '已更新系统信息', DATE_SUB(NOW(), INTERVAL 3 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050035');

-- 唐嫣（财务部员工）的工单
SET @user_tangyan = (SELECT id FROM sys_user WHERE username = 'tangyan' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050036', '考勤异常', '忘打卡申请', '早上忘记打卡', 'pending', @user_tangyan, @user_yangmi, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050036');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050037', '请假申请', '病假申请', '身体不适', 'completed', @user_tangyan, @user_yangmi, '已批准', DATE_SUB(NOW(), INTERVAL 4 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 6 DAY), DATE_SUB(NOW(), INTERVAL 4 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050037');

-- 刘诗诗（财务部员工）的工单
SET @user_liushishi = (SELECT id FROM sys_user WHERE username = 'liushishi' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050038', '其他', 'IT设备申请', '申请新的键盘鼠标', 'pending', @user_liushishi, @user_yangmi, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050038');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050039', '证明开具', '在职证明申请', '需要开具在职证明', 'completed', @user_liushishi, @user_yangmi, '已开具', DATE_SUB(NOW(), INTERVAL 2 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050039');

-- 黄渤（行政部HR）的工单
SET @user_huangbo = (SELECT id FROM sys_user WHERE username = 'huangbo' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050040', '请假申请', '事假申请', '家中有事', 'pending', @user_huangbo, NULL, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050040');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050041', '信息变更', '手机号码变更', '更换手机号码', 'completed', @user_huangbo, NULL, '已更新系统信息', DATE_SUB(NOW(), INTERVAL 2 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050041');

-- 徐峥（行政部员工）的工单
SET @user_xuzheng = (SELECT id FROM sys_user WHERE username = 'xuzheng' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050042', '考勤异常', '迟到说明', '交通堵塞', 'pending', @user_xuzheng, @user_huangbo, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050042');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050043', '报销薪资', '办公用品报销', '购买办公用品', 'completed', @user_xuzheng, @user_huangbo, '已审批通过', DATE_SUB(NOW(), INTERVAL 3 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050043');

-- 王宝强（行政部员工）的工单
SET @user_wangbaoqiang = (SELECT id FROM sys_user WHERE username = 'wangbaoqiang' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050044', '请假申请', '年假申请', '申请年假', 'pending', @user_wangbaoqiang, @user_huangbo, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050044');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050045', '其他', '会议室预定', '需要预定会议室', 'completed', @user_wangbaoqiang, @user_huangbo, '已预定', DATE_SUB(NOW(), INTERVAL 1 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050045');

-- 邓超（行政部员工）的工单
SET @user_dengchao = (SELECT id FROM sys_user WHERE username = 'dengchao' LIMIT 1);

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050046', '证明开具', '收入证明申请', '需要开具收入证明', 'pending', @user_dengchao, @user_huangbo, NULL, NULL, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050046');

INSERT INTO biz_ticket (ticket_no, type, title, description, status, creator_id, assignee_id, resolve_note, resolved_at, conversation_id, created_at, updated_at)
SELECT 'TK202607050047', '信息变更', '银行卡号变更', '更换工资卡', 'completed', @user_dengchao, @user_huangbo, '已更新系统信息', DATE_SUB(NOW(), INTERVAL 2 DAY), UUID(), DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_ticket WHERE ticket_no = 'TK202607050047');

-- =====================================================
-- 4. 创建公告
-- =====================================================

-- 公告1：年假安排通知
INSERT INTO sys_notice (title, content, notice_type, is_pinned, publisher_id, expire_at, created_at)
SELECT '关于2026年年假安排的通知', '各位同事：\n\n根据公司规定，2026年年假安排如下：\n1. 年假有效期为2026年1月1日至2026年12月31日\n2. 请各部门合理安排员工休假计划\n3. 年假需提前3天申请\n\n特此通知。', 'general', 1, @user_zhangsan, DATE_ADD(NOW(), INTERVAL 30 DAY), DATE_SUB(NOW(), INTERVAL 7 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_notice WHERE title = '关于2026年年假安排的通知');

SET @notice_1 = (SELECT id FROM sys_notice WHERE title = '关于2026年年假安排的通知' LIMIT 1);

-- 公告2：团建活动通知
INSERT INTO sys_notice (title, content, notice_type, is_pinned, publisher_id, expire_at, created_at)
SELECT '公司团建活动通知', '各位同事：\n\n为增进同事间的交流与合作，公司定于7月20日组织团建活动。\n活动地点：XX拓展基地\n集合时间：早上8:30\n请各位同事准时参加。', 'activity', 0, @user_liudehua, DATE_ADD(NOW(), INTERVAL 20 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_notice WHERE title = '公司团建活动通知');

SET @notice_2 = (SELECT id FROM sys_notice WHERE title = '公司团建活动通知' LIMIT 1);

-- 公告3：考勤管理通知
INSERT INTO sys_notice (title, content, notice_type, is_pinned, publisher_id, expire_at, created_at)
SELECT '关于规范考勤管理的通知', '各位同事：\n\n为加强公司考勤管理，现将有关事项通知如下：\n1. 工作时间为上午9:00-12:00，下午13:30-18:00\n2. 迟到30分钟以内需说明原因\n3. 请务必按时打卡\n\n特此通知。', 'policy', 1, @user_chenglong, DATE_ADD(NOW(), INTERVAL 60 DAY), DATE_SUB(NOW(), INTERVAL 14 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_notice WHERE title = '关于规范考勤管理的通知');

SET @notice_3 = (SELECT id FROM sys_notice WHERE title = '关于规范考勤管理的通知' LIMIT 1);

-- 公告4：系统维护通知
INSERT INTO sys_notice (title, content, notice_type, is_pinned, publisher_id, expire_at, created_at)
SELECT '系统维护通知', '各位同事：\n\n公司OA系统将于本周六（7月11日）22:00至次日6:00进行维护升级，届时系统将暂停服务。\n请各位同事提前做好相关工作安排。\n\n给您带来不便，敬请谅解。', 'system', 0, @user_yangmi, DATE_ADD(NOW(), INTERVAL 10 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_notice WHERE title = '系统维护通知');

SET @notice_4 = (SELECT id FROM sys_notice WHERE title = '系统维护通知' LIMIT 1);

-- 公告5：端午节放假通知
INSERT INTO sys_notice (title, content, notice_type, is_pinned, publisher_id, expire_at, created_at)
SELECT '关于端午节放假安排的通知', '各位同事：\n\n根据国家法定节假日安排，端午节放假时间为6月25日至6月27日，共3天。\n6月28日（周日）正常上班。\n请各部门做好工作安排。\n\n祝大家端午节快乐！', 'holiday', 1, @user_huangbo, DATE_ADD(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 10 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_notice WHERE title = '关于端午节放假安排的通知');

SET @notice_5 = (SELECT id FROM sys_notice WHERE title = '关于端午节放假安排的通知' LIMIT 1);

-- 创建公告已读记录（部分用户已读）
-- 公告1的已读记录
INSERT INTO sys_notice_read (notice_id, user_id, read_at)
SELECT @notice_1, @user_lisi, DATE_SUB(NOW(), INTERVAL 6 DAY)
FROM DUAL
WHERE @notice_1 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sys_notice_read WHERE notice_id = @notice_1 AND user_id = @user_lisi);

INSERT INTO sys_notice_read (notice_id, user_id, read_at)
SELECT @notice_1, @user_wangwu, DATE_SUB(NOW(), INTERVAL 5 DAY)
FROM DUAL
WHERE @notice_1 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sys_notice_read WHERE notice_id = @notice_1 AND user_id = @user_wangwu);

INSERT INTO sys_notice_read (notice_id, user_id, read_at)
SELECT @notice_1, @user_zhangxueyou, DATE_SUB(NOW(), INTERVAL 6 DAY)
FROM DUAL
WHERE @notice_1 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sys_notice_read WHERE notice_id = @notice_1 AND user_id = @user_zhangxueyou);

INSERT INTO sys_notice_read (notice_id, user_id, read_at)
SELECT @notice_1, @user_guofucheng, DATE_SUB(NOW(), INTERVAL 4 DAY)
FROM DUAL
WHERE @notice_1 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sys_notice_read WHERE notice_id = @notice_1 AND user_id = @user_guofucheng);

INSERT INTO sys_notice_read (notice_id, user_id, read_at)
SELECT @notice_1, @user_zhaoliying, DATE_SUB(NOW(), INTERVAL 5 DAY)
FROM DUAL
WHERE @notice_1 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sys_notice_read WHERE notice_id = @notice_1 AND user_id = @user_zhaoliying);

-- 公告2的已读记录
INSERT INTO sys_notice_read (notice_id, user_id, read_at)
SELECT @notice_2, @user_liming, DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE @notice_2 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sys_notice_read WHERE notice_id = @notice_2 AND user_id = @user_liming);

INSERT INTO sys_notice_read (notice_id, user_id, read_at)
SELECT @notice_2, @user_zhoujielun, DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE @notice_2 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sys_notice_read WHERE notice_id = @notice_2 AND user_id = @user_zhoujielun);

INSERT INTO sys_notice_read (notice_id, user_id, read_at)
SELECT @notice_2, @user_lianjie, DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE @notice_2 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sys_notice_read WHERE notice_id = @notice_2 AND user_id = @user_lianjie);

-- 公告3的已读记录
INSERT INTO sys_notice_read (notice_id, user_id, read_at)
SELECT @notice_3, @user_lisi, DATE_SUB(NOW(), INTERVAL 13 DAY)
FROM DUAL
WHERE @notice_3 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sys_notice_read WHERE notice_id = @notice_3 AND user_id = @user_lisi);

INSERT INTO sys_notice_read (notice_id, user_id, read_at)
SELECT @notice_3, @user_xuzheng, DATE_SUB(NOW(), INTERVAL 12 DAY)
FROM DUAL
WHERE @notice_3 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sys_notice_read WHERE notice_id = @notice_3 AND user_id = @user_xuzheng);

-- =====================================================
-- 5. 创建问答记录
-- =====================================================

-- 张三的问答记录
INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_zhangsan, '年假有多少天？', '根据公司规定，员工年假天数如下：\n- 工作满1年不满10年：5天\n- 工作满10年不满20年：10天\n- 工作满20年：15天\n年假有效期为当年1月1日至12月31日，过期作废。', 'rag', NULL, 1, 0, UUID(), DATE_SUB(NOW(), INTERVAL 5 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_zhangsan AND question = '年假有多少天？');

INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_zhangsan, '如何申请报销？', '申请报销的流程如下：\n1. 登录HR系统\n2. 选择"报销申请"功能\n3. 填写报销类型、金额、事由\n4. 上传发票照片\n5. 提交等待审批\n\n审批通过后，报销款项将在5个工作日内打到您的工资卡。', 'rag', NULL, 1, 1, UUID(), DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_zhangsan AND question = '如何申请报销？');

-- 李四的问答记录
INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_lisi, '公司有什么福利？', '公司提供的福利包括：\n1. 五险一金\n2. 补充商业保险\n3. 年度体检\n4. 节日礼品\n5. 生日福利\n6. 带薪年假\n7. 员工培训\n8. 团建活动\n具体可查看员工手册。', 'rag', NULL, 1, 0, UUID(), DATE_SUB(NOW(), INTERVAL 4 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_lisi AND question = '公司有什么福利？');

INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_lisi, '试用期多久？', '公司试用期规定：\n- 劳动合同期限1年以上不满3年：试用期2个月\n- 劳动合同期限3年以上：试用期6个月\n试用期内享受正式员工80%的工资待遇。', 'rag', NULL, -1, 0, UUID(), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_lisi AND question = '试用期多久？');

INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_lisi, '如何请假？', '请假流程：\n1. 提前在HR系统提交请假申请\n2. 选择请假类型（年假/事假/病假等）\n3. 填写请假时间和原因\n4. 提交审批\n\n请假审批流程：\n- 1天以内：直属主管审批\n- 1-3天：部门经理审批\n- 3天以上：HR总监审批', 'rag', NULL, 1, 0, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_lisi AND question = '如何请假？');

-- 刘德华的问答记录
INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_liudehua, '工资什么时候发？', '公司工资发放规定：\n- 发放日期：每月15日\n- 如遇节假日则提前发放\n- 工资通过银行转账方式发放到个人工资卡\n- 工资条可在HR系统中查看', 'rag', NULL, 1, 0, UUID(), DATE_SUB(NOW(), INTERVAL 6 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_liudehua AND question = '工资什么时候发？');

INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_liudehua, '如何开具在职证明？', '开具在职证明的步骤：\n1. 登录HR系统\n2. 选择"证明开具"功能\n3. 选择证明类型（在职证明/收入证明等）\n4. 填写用途和接收单位\n5. 提交申请\n\n一般1-3个工作日内可领取。', 'rag', NULL, 1, 1, UUID(), DATE_SUB(NOW(), INTERVAL 4 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_liudehua AND question = '如何开具在职证明？');

INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_liudehua, '加班如何计算？', '加班计算标准：\n- 工作日加班：1.5倍工资\n- 周末加班：2倍工资\n- 法定节假日：3倍工资\n\n加班需提前申请并经主管批准。加班时间可选择调休或发放加班费。', 'rag', NULL, -1, 0, UUID(), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_liudehua AND question = '加班如何计算？');

-- 张学友的问答记录
INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_zhangxueyou, '年假有多少天？', '根据公司规定，员工年假天数如下：\n- 工作满1年不满10年：5天\n- 工作满10年不满20年：10天\n- 工作满20年：15天\n年假有效期为当年1月1日至12月31日，过期作废。', 'rag', NULL, 1, 0, UUID(), DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_zhangxueyou AND question = '年假有多少天？');

INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_zhangxueyou, '如何申请报销？', '申请报销的流程如下：\n1. 登录HR系统\n2. 选择"报销申请"功能\n3. 填写报销类型、金额、事由\n4. 上传发票照片\n5. 提交等待审批\n\n审批通过后，报销款项将在5个工作日内打到您的工资卡。', 'rag', NULL, 1, 0, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_zhangxueyou AND question = '如何申请报销？');

-- 成龙的问答记录
INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_chenglong, '如何请假？', '请假流程：\n1. 提前在HR系统提交请假申请\n2. 选择请假类型（年假/事假/病假等）\n3. 填写请假时间和原因\n4. 提交审批\n\n请假审批流程：\n- 1天以内：直属主管审批\n- 1-3天：部门经理审批\n- 3天以上：HR总监审批', 'rag', NULL, 1, 0, UUID(), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_chenglong AND question = '如何请假？');

INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_chenglong, '公司有什么福利？', '公司提供的福利包括：\n1. 五险一金\n2. 补充商业保险\n3. 年度体检\n4. 节日礼品\n5. 生日福利\n6. 带薪年假\n7. 员工培训\n8. 团建活动\n具体可查看员工手册。', 'rag', NULL, 1, 1, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_chenglong AND question = '公司有什么福利？');

-- 杨幂的问答记录
INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_yangmi, '工资什么时候发？', '公司工资发放规定：\n- 发放日期：每月15日\n- 如遇节假日则提前发放\n- 工资通过银行转账方式发放到个人工资卡\n- 工资条可在HR系统中查看', 'rag', NULL, 1, 0, UUID(), DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_yangmi AND question = '工资什么时候发？');

INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_yangmi, '如何开具在职证明？', '开具在职证明的步骤：\n1. 登录HR系统\n2. 选择"证明开具"功能\n3. 选择证明类型（在职证明/收入证明等）\n4. 填写用途和接收单位\n5. 提交申请\n\n一般1-3个工作日内可领取。', 'rag', NULL, 1, 0, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_yangmi AND question = '如何开具在职证明？');

-- 黄渤的问答记录
INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_huangbo, '加班如何计算？', '加班计算标准：\n- 工作日加班：1.5倍工资\n- 周末加班：2倍工资\n- 法定节假日：3倍工资\n\n加班需提前申请并经主管批准。加班时间可选择调休或发放加班费。', 'rag', NULL, 1, 0, UUID(), DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_huangbo AND question = '加班如何计算？');

INSERT INTO qa_record (user_id, question, answer, answer_type, source_docs, feedback, is_favorite, conversation_id, created_at)
SELECT @user_huangbo, '试用期多久？', '公司试用期规定：\n- 劳动合同期限1年以上不满3年：试用期2个月\n- 劳动合同期限3年以上：试用期6个月\n试用期内享受正式员工80%的工资待遇。', 'rag', NULL, 1, 1, UUID(), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_record WHERE user_id = @user_huangbo AND question = '试用期多久？');

-- =====================================================
-- 6. 创建问答反馈
-- =====================================================

-- 为李四的负面反馈创建反馈记录
SET @qa_lisi_probation = (SELECT id FROM qa_record WHERE user_id = @user_lisi AND question = '试用期多久？' LIMIT 1);

INSERT INTO qa_feedback (record_id, user_id, feedback_type, correction_text, status, handler_id, handle_note, created_at, handled_at)
SELECT @qa_lisi_probation, @user_lisi, 'incorrect', '回答不够准确，需要更新', 'processed', @user_zhangsan, '已更新知识库', DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE @qa_lisi_probation IS NOT NULL AND NOT EXISTS (SELECT 1 FROM qa_feedback WHERE record_id = @qa_lisi_probation);

-- 为刘德华的负面反馈创建反馈记录
SET @qa_liudehua_overtime = (SELECT id FROM qa_record WHERE user_id = @user_liudehua AND question = '加班如何计算？' LIMIT 1);

INSERT INTO qa_feedback (record_id, user_id, feedback_type, correction_text, status, handler_id, handle_note, created_at, handled_at)
SELECT @qa_liudehua_overtime, @user_liudehua, 'incorrect', '加班政策有更新', 'pending', NULL, NULL, DATE_SUB(NOW(), INTERVAL 2 DAY), NULL
FROM DUAL
WHERE @qa_liudehua_overtime IS NOT NULL AND NOT EXISTS (SELECT 1 FROM qa_feedback WHERE record_id = @qa_liudehua_overtime);

-- =====================================================
-- 6.5 人力资源部反馈处理数据（新增）
-- =====================================================
-- HR部门员工：张三(id=zhangsan, HR)、李四(id=lisi, 员工)、王五(id=wangwu, 员工)
-- 反馈由李四和王五提交，张三作为HR处理

-- 反馈1：李四 - 产假政策回答不准确（已处理）
SET @qa_lisi_maternity = (SELECT id FROM qa_record WHERE user_id = @user_lisi AND question = '公司有什么福利？' LIMIT 1);

INSERT INTO qa_feedback (record_id, user_id, feedback_type, correction_text, status, handler_id, handle_note, created_at, handled_at, department_id)
SELECT @qa_lisi_maternity, @user_lisi, 'incorrect',
    '回答中未提及最新的产假政策。根据2025年新修订的《女职工劳动保护特别规定》，产假已从98天延长至158天，难产增加15天，多胞胎每多一个增加15天。公司已在2025年9月更新了内部制度，但系统回答仍然缺失。',
    'resolved', @user_zhangsan, '已核实：知识库中福利概览文档未同步2025年产假新规。已更新《员工福利手册》第3章第2节产假条款，并通知文档管理员重新索引。',
    DATE_SUB(NOW(), INTERVAL 6 DAY), DATE_SUB(NOW(), INTERVAL 4 DAY), @dept_hr
FROM DUAL
WHERE @qa_lisi_maternity IS NOT NULL AND NOT EXISTS (SELECT 1 FROM qa_feedback WHERE record_id = @qa_lisi_maternity AND feedback_type = 'incorrect');

-- 反馈2：王五 - 报销流程说明过时（已处理）
SET @qa_wangwu_reimburse = (SELECT id FROM qa_record WHERE user_id = @user_zhangsan AND question = '如何申请报销？' LIMIT 1);

INSERT INTO qa_feedback (record_id, user_id, feedback_type, correction_text, status, handler_id, handle_note, created_at, handled_at, department_id)
SELECT @qa_wangwu_reimburse, @user_wangwu, 'incorrect',
    '系统回答称报销审批通过后5个工作日内到账，但实际上从2026年1月起公司已改为每周三集中打款，到账时间为审批通过后3-7个工作日不等。另外，回答未提及超过5000元的报销需要部门总监额外审批这一新规定。',
    'resolved', @user_zhangsan, '已确认：财务部2026年1月发布了新的报销打款流程。已更新《报销管理制度》文档，并在知识库中标记旧流程为过时版本。',
    DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY), @dept_hr
FROM DUAL
WHERE @qa_wangwu_reimburse IS NOT NULL AND NOT EXISTS (SELECT 1 FROM qa_feedback WHERE record_id = @qa_wangwu_reimburse AND user_id = @user_wangwu);

-- 反馈3：李四 - 请假审批层级描述模糊（处理中）
SET @qa_lisi_leave = (SELECT id FROM qa_record WHERE user_id = @user_lisi AND question = '如何请假？' LIMIT 1);

INSERT INTO qa_feedback (record_id, user_id, feedback_type, correction_text, status, handler_id, handle_note, created_at, handled_at, department_id)
SELECT @qa_lisi_leave, @user_lisi, 'incorrect',
    '回答中"1天以内直属主管审批"的表述不够准确。实际上，公司2025年11月更新的《考勤管理制度》规定：事假1天以内由直属主管审批，但病假无论天数均需提供医院证明并由部门经理审批。年假则统一由直属主管审批，无需额外层级。当前回答将不同类型假期的审批流程混为一谈，容易造成误导。',
    'processed', @user_zhangsan, '已确认反馈属实，正在与制度文件逐条核对中。计划将请假政策按假期类型分别整理，预计本周内完成知识库更新。',
    DATE_SUB(NOW(), INTERVAL 3 DAY), NULL, @dept_hr
FROM DUAL
WHERE @qa_lisi_leave IS NOT NULL AND NOT EXISTS (SELECT 1 FROM qa_feedback WHERE record_id = @qa_lisi_leave AND user_id = @user_lisi AND feedback_type = 'incorrect');

-- 反馈4：王五 - 加班调休政策缺失（待处理）
SET @qa_wangwu_overtime = (SELECT id FROM qa_record WHERE user_id = @user_liudehua AND question = '加班如何计算？' LIMIT 1);

INSERT INTO qa_feedback (record_id, user_id, feedback_type, correction_text, status, handler_id, handle_note, created_at, handled_at, department_id)
SELECT @qa_wangwu_overtime, @user_wangwu, 'useless',
    '回答只提到了加班费的倍数计算，但完全没有说明调休的使用规则。很多同事更关心的是：调休是否有有效期？调休和加班费能否同时选择？跨月加班如何处理？这些才是大家最常问的问题，建议补充完善。',
    'pending', NULL, NULL,
    DATE_SUB(NOW(), INTERVAL 1 DAY), NULL, @dept_hr
FROM DUAL
WHERE @qa_wangwu_overtime IS NOT NULL AND NOT EXISTS (SELECT 1 FROM qa_feedback WHERE record_id = @qa_wangwu_overtime AND user_id = @user_wangwu);

-- 反馈5：李四 - 试用期工资比例说明有误（已处理，关联已有反馈）
-- 补充张三对已有李四试用期反馈的AI建议记录
UPDATE qa_feedback
SET ai_suggestion = '建议更新试用期政策文档，明确以下要点：1）试用期工资不得低于本单位相同岗位最低档工资的80%或劳动合同约定工资的80%；2）试用期工资不得低于用人单位所在地的最低工资标准。建议引用《劳动合同法》第二十条原文以增强权威性。',
    ai_suggestion_at = DATE_SUB(NOW(), INTERVAL 1 DAY),
    department_id = @dept_hr
WHERE record_id = @qa_lisi_probation AND feedback_type = 'incorrect' AND department_id IS NULL;

-- 反馈6：王五 - 福利概览缺少补充医疗险说明（已处理）
SET @qa_wangwu_welfare = (SELECT id FROM qa_record WHERE user_id = @user_lisi AND question = '公司有什么福利？' LIMIT 1);

INSERT INTO qa_feedback (record_id, user_id, feedback_type, correction_text, status, handler_id, handle_note, created_at, handled_at, department_id)
SELECT @qa_wangwu_welfare, @user_wangwu, 'useless',
    '回答中列出了"补充商业保险"但没有详细说明保障范围。同事们经常问：门诊能不能报销？牙科和眼科包不包含？家属能不能一起参保？这些信息在知识库里找不到，导致大家每次都得来问HR。',
    'resolved', @user_zhangsan, '已联系保险公司获取最新的团体险保障方案明细，整理为《补充商业保险FAQ》文档并上传至知识库。包含门诊/住院/牙科/眼科/家属参保等12个常见问题。',
    DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY), @dept_hr
FROM DUAL
WHERE @qa_wangwu_welfare IS NOT NULL AND NOT EXISTS (SELECT 1 FROM qa_feedback WHERE record_id = @qa_wangwu_welfare AND user_id = @user_wangwu);

-- =====================================================
-- 7. 创建未命中问题（知识缺口）
-- =====================================================
-- HR部门相关知识缺口，由HR部门员工使用系统时产生

INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_lisi, '公司有没有健身房？', 1, 0, DATE_SUB(NOW(), INTERVAL 3 DAY), @dept_hr
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_lisi AND question = '公司有没有健身房？');

INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_wangwu, '如何申请加班餐补？', 2, 0, DATE_SUB(NOW(), INTERVAL 2 DAY), @dept_hr
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_wangwu AND question = '如何申请加班餐补？');

INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_zhangxueyou, '年假可以跨年使用吗？', 1, 1, DATE_SUB(NOW(), INTERVAL 5 DAY), @dept_tech
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_zhangxueyou AND question = '年假可以跨年使用吗？');

INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_guofucheng, '公司有班车吗？', 3, 0, DATE_SUB(NOW(), INTERVAL 4 DAY), @dept_tech
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_guofucheng AND question = '公司有班车吗？');

INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_lianjie, '公积金缴纳比例是多少？', 4, 0, DATE_SUB(NOW(), INTERVAL 3 DAY), @dept_market
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_lianjie AND question = '公积金缴纳比例是多少？');

INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_zhaoliying, '公司有员工宿舍吗？', 3, 0, DATE_SUB(NOW(), INTERVAL 2 DAY), @dept_finance
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_zhaoliying AND question = '公司有员工宿舍吗？');

INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_xuzheng, '如何申请调岗？', 5, 0, DATE_SUB(NOW(), INTERVAL 1 DAY), @dept_admin
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_xuzheng AND question = '如何申请调岗？');

-- HR部门新增知识缺口（7条）
INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_lisi, '公司内部转岗流程是什么？', 6, 0, DATE_SUB(NOW(), INTERVAL 5 DAY), @dept_hr
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_lisi AND question = '公司内部转岗流程是什么？');

INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_wangwu, '员工子女教育补贴怎么申请？', 7, 0, DATE_SUB(NOW(), INTERVAL 4 DAY), @dept_hr
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_wangwu AND question = '员工子女教育补贴怎么申请？');

INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_lisi, '离职需要提前多久通知公司？', 8, 1, DATE_SUB(NOW(), INTERVAL 7 DAY), @dept_hr
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_lisi AND question = '离职需要提前多久通知公司？');

INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_wangwu, '异地就医医保怎么报销？', 9, 0, DATE_SUB(NOW(), INTERVAL 3 DAY), @dept_hr
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_wangwu AND question = '异地就医医保怎么报销？');

INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_lisi, '竞业限制协议的补偿标准是多少？', 10, 0, DATE_SUB(NOW(), INTERVAL 6 DAY), @dept_hr
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_lisi AND question = '竞业限制协议的补偿标准是多少？');

INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_wangwu, '工伤认定的流程和时限是什么？', 11, 0, DATE_SUB(NOW(), INTERVAL 2 DAY), @dept_hr
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_wangwu AND question = '工伤认定的流程和时限是什么？');

INSERT INTO qa_miss (user_id, question, cluster_id, resolved, created_at, department_id)
SELECT @user_lisi, '员工培训费用由谁承担？', 12, 0, DATE_SUB(NOW(), INTERVAL 1 DAY), @dept_hr
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM qa_miss WHERE user_id = @user_lisi AND question = '员工培训费用由谁承担？');

-- =====================================================
-- 8. 创建评论（针对工单的评论）
-- =====================================================

-- 为部分工单创建评论
SET @ticket_1 = (SELECT id FROM biz_ticket WHERE ticket_no = 'TK202607050001' LIMIT 1);
SET @ticket_4 = (SELECT id FROM biz_ticket WHERE ticket_no = 'TK202607050004' LIMIT 1);
SET @ticket_5 = (SELECT id FROM biz_ticket WHERE ticket_no = 'TK202607050005' LIMIT 1);
SET @ticket_11 = (SELECT id FROM biz_ticket WHERE ticket_no = 'TK202607050011' LIMIT 1);
SET @ticket_12 = (SELECT id FROM biz_ticket WHERE ticket_no = 'TK202607050012' LIMIT 1);
SET @ticket_14 = (SELECT id FROM biz_ticket WHERE ticket_no = 'TK202607050014' LIMIT 1);
SET @ticket_24 = (SELECT id FROM biz_ticket WHERE ticket_no = 'TK202607050024' LIMIT 1);
SET @ticket_25 = (SELECT id FROM biz_ticket WHERE ticket_no = 'TK202607050025' LIMIT 1);
SET @ticket_34 = (SELECT id FROM biz_ticket WHERE ticket_no = 'TK202607050034' LIMIT 1);
SET @ticket_42 = (SELECT id FROM biz_ticket WHERE ticket_no = 'TK202607050042' LIMIT 1);

-- 工单1的评论
INSERT INTO biz_comment (target_type, target_id, user_id, content, like_count, is_adopted, status, created_at)
SELECT 'ticket', @ticket_1, @user_zhangsan, '已批准，请注意休假期间的工作交接。', 2, 0, 1, DATE_SUB(NOW(), INTERVAL 4 DAY)
FROM DUAL
WHERE @ticket_1 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM biz_comment WHERE target_type = 'ticket' AND target_id = @ticket_1 AND user_id = @user_zhangsan);

-- 工单4的评论
INSERT INTO biz_comment (target_type, target_id, user_id, content, like_count, is_adopted, status, created_at)
SELECT 'ticket', @ticket_4, @user_zhangsan, '请补充打卡记录截图。', 1, 0, 1, DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE @ticket_4 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM biz_comment WHERE target_type = 'ticket' AND target_id = @ticket_4 AND user_id = @user_zhangsan);

INSERT INTO biz_comment (target_type, target_id, user_id, content, like_count, is_adopted, status, created_at)
SELECT 'ticket', @ticket_4, @user_lisi, '好的，已上传截图。', 0, 0, 1, DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 2 HOUR
FROM DUAL
WHERE @ticket_4 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM biz_comment WHERE target_type = 'ticket' AND target_id = @ticket_4 AND user_id = @user_lisi);

-- 工单5的评论
INSERT INTO biz_comment (target_type, target_id, user_id, content, like_count, is_adopted, status, created_at)
SELECT 'ticket', @ticket_5, @user_zhangsan, '发票已收到，审批已通过。', 3, 1, 1, DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE @ticket_5 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM biz_comment WHERE target_type = 'ticket' AND target_id = @ticket_5 AND user_id = @user_zhangsan);

-- 工单11的评论
INSERT INTO biz_comment (target_type, target_id, user_id, content, like_count, is_adopted, status, created_at)
SELECT 'ticket', @ticket_11, @user_liudehua, '请问迟到多久？', 0, 0, 1, DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE @ticket_11 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM biz_comment WHERE target_type = 'ticket' AND target_id = @ticket_11 AND user_id = @user_liudehua);

INSERT INTO biz_comment (target_type, target_id, user_id, content, like_count, is_adopted, status, created_at)
SELECT 'ticket', @ticket_11, @user_zhangxueyou, '大约15分钟。', 0, 0, 1, DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 1 HOUR
FROM DUAL
WHERE @ticket_11 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM biz_comment WHERE target_type = 'ticket' AND target_id = @ticket_11 AND user_id = @user_zhangxueyou);

-- 工单12的评论
INSERT INTO biz_comment (target_type, target_id, user_id, content, like_count, is_adopted, status, created_at)
SELECT 'ticket', @ticket_12, @user_liudehua, '已审批通过，报销款将尽快打到您的工资卡。', 2, 1, 1, DATE_SUB(NOW(), INTERVAL 4 DAY)
FROM DUAL
WHERE @ticket_12 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM biz_comment WHERE target_type = 'ticket' AND target_id = @ticket_12 AND user_id = @user_liudehua);

-- 工单14的评论
INSERT INTO biz_comment (target_type, target_id, user_id, content, like_count, is_adopted, status, created_at)
SELECT 'ticket', @ticket_14, @user_liudehua, '年假已批准，请做好工作交接。', 1, 0, 1, DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE @ticket_14 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM biz_comment WHERE target_type = 'ticket' AND target_id = @ticket_14 AND user_id = @user_liudehua);

-- 工单24的评论
INSERT INTO biz_comment (target_type, target_id, user_id, content, like_count, is_adopted, status, created_at)
SELECT 'ticket', @ticket_24, @user_chenglong, '收到，会尽快处理。', 0, 0, 1, DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE @ticket_24 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM biz_comment WHERE target_type = 'ticket' AND target_id = @ticket_24 AND user_id = @user_chenglong);

-- 工单25的评论
INSERT INTO biz_comment (target_type, target_id, user_id, content, like_count, is_adopted, status, created_at)
SELECT 'ticket', @ticket_25, @user_chenglong, '报销已审批通过。', 2, 1, 1, DATE_SUB(NOW(), INTERVAL 3 DAY)
FROM DUAL
WHERE @ticket_25 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM biz_comment WHERE target_type = 'ticket' AND target_id = @ticket_25 AND user_id = @user_chenglong);

-- 工单34的评论
INSERT INTO biz_comment (target_type, target_id, user_id, content, like_count, is_adopted, status, created_at)
SELECT 'ticket', @ticket_34, @user_yangmi, '请补充发票照片。', 0, 0, 1, DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE @ticket_34 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM biz_comment WHERE target_type = 'ticket' AND target_id = @ticket_34 AND user_id = @user_yangmi);

INSERT INTO biz_comment (target_type, target_id, user_id, content, like_count, is_adopted, status, created_at)
SELECT 'ticket', @ticket_34, @user_zhaoliying, '好的，已上传。', 0, 0, 1, DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 3 HOUR
FROM DUAL
WHERE @ticket_34 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM biz_comment WHERE target_type = 'ticket' AND target_id = @ticket_34 AND user_id = @user_zhaoliying);

-- 工单42的评论
INSERT INTO biz_comment (target_type, target_id, user_id, content, like_count, is_adopted, status, created_at)
SELECT 'ticket', @ticket_42, @user_huangbo, '收到，会尽快处理。', 1, 0, 1, DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM DUAL
WHERE @ticket_42 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM biz_comment WHERE target_type = 'ticket' AND target_id = @ticket_42 AND user_id = @user_huangbo);

-- =====================================================
-- 9. 创建提醒规则
-- =====================================================

INSERT INTO biz_reminder_rule (name, rule_type, trigger_days, target_role, channels, template, is_active, created_at)
SELECT '合同到期提醒', 'contract', 30, 'employee', 'site,email', '您的合同将于{days}天后到期，请及时续签。', 1, NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_reminder_rule WHERE name = '合同到期提醒');

INSERT INTO biz_reminder_rule (name, rule_type, trigger_days, target_role, channels, template, is_active, created_at)
SELECT '试用期到期提醒', 'probation', 7, 'employee', 'site,email', '您的试用期将于{days}天后到期，请做好转正准备。', 1, NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_reminder_rule WHERE name = '试用期到期提醒');

INSERT INTO biz_reminder_rule (name, rule_type, trigger_days, target_role, channels, template, is_active, created_at)
SELECT '年假清零提醒', 'annual_leave', 30, 'employee', 'site', '您还有{days}天年假未使用，请合理安排。', 1, NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM biz_reminder_rule WHERE name = '年假清零提醒');

-- =====================================================
-- 数据统计
-- =====================================================

-- 统计各部门用户数
SELECT '📊 数据统计' AS '统计项';
SELECT '部门' AS '类型', COUNT(*) AS '数量' FROM sys_department
UNION ALL
SELECT '用户', COUNT(*) FROM sys_user
UNION ALL
SELECT '工单', COUNT(*) FROM biz_ticket
UNION ALL
SELECT '公告', COUNT(*) FROM sys_notice
UNION ALL
SELECT '问答记录', COUNT(*) FROM qa_record
UNION ALL
SELECT '问答反馈', COUNT(*) FROM qa_feedback
UNION ALL
SELECT '评论', COUNT(*) FROM biz_comment
UNION ALL
SELECT '未命中问题', COUNT(*) FROM qa_miss;

-- 统计各部门用户分布
SELECT d.name AS '部门',
       COUNT(u.id) AS '总人数',
       SUM(CASE WHEN u.role = 'hr' THEN 1 ELSE 0 END) AS 'HR人数',
       SUM(CASE WHEN u.role = 'employee' THEN 1 ELSE 0 END) AS '员工人数'
FROM sys_department d
LEFT JOIN sys_user u ON d.id = u.department_id
GROUP BY d.id, d.name
ORDER BY d.sort_order;

-- 统计各类型工单数量
SELECT type AS '工单类型', COUNT(*) AS '数量'
FROM biz_ticket
GROUP BY type
ORDER BY COUNT(*) DESC;

-- 统计工单状态分布
SELECT status AS '状态', COUNT(*) AS '数量'
FROM biz_ticket
GROUP BY status;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- 脚本执行完成
-- =====================================================
SELECT '✅ 测试数据初始化完成！' AS '状态';
SELECT '默认密码: 123456' AS '提示';
