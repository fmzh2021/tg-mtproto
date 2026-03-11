#!/bin/bash
# 项目验证脚本 - 快速检查项目配置是否完整

echo "=================================================="
echo "Telethon 聊天同步工具 - 项目验证"
echo "=================================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数
PASSED=0
FAILED=0
WARNINGS=0

# 检查文件是否存在
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} 找到：$1"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} 缺失：$1"
        ((FAILED++))
    fi
}

# 检查目录是否存在
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} 找到目录：$1"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} 目录不存在：$1 (可选)"
        ((WARNINGS++))
    fi
}

echo "1. 检查核心程序文件..."
check_file "main.py"
check_file "config.py"
check_file "message_storage.py"
check_file "query_messages.py"

echo ""
echo "2. 检查示例和测试文件..."
check_file "quick_start.py"
check_file "test_basic.py"

echo ""
echo "3. 检查配置文件..."
check_file "requirements.txt"
check_file ".env.example"
check_file ".gitignore"

echo ""
echo "4. 检查文档..."
check_file "README.md"
check_file "USAGE.md"
check_file "PROJECT_SUMMARY.md"

echo ""
echo "5. 检查虚拟环境..."
check_dir "venv"

echo ""
echo "6. 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} Python3 已安装：$(python3 --version)"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} Python3 未安装"
    ((FAILED++))
fi

echo ""
echo "7. 检查依赖包..."
if [ -d "venv" ]; then
    source venv/bin/activate
    if python -c "import telethon" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Telethon 已安装"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} Telethon 未安装，运行：pip install -r requirements.txt"
        ((WARNINGS++))
    fi
    
    if python -c "import dotenv" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} python-dotenv 已安装"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} python-dotenv 未安装，运行：pip install python-dotenv"
        ((WARNINGS++))
    fi
    deactivate
else
    echo -e "${YELLOW}⚠${NC} 虚拟环境不存在，先创建虚拟环境"
    ((WARNINGS++))
fi

echo ""
echo "8. 检查环境配置..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env 文件已配置"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠${NC} .env 文件不存在，请复制 .env.example 并配置"
    ((WARNINGS++))
fi

echo ""
echo "=================================================="
echo "验证结果汇总"
echo "=================================================="
echo -e "通过：${GREEN}${PASSED}${NC}"
echo -e "失败：${RED}${FAILED}${NC}"
echo -e "警告：${YELLOW}${WARNINGS}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 项目配置完整！${NC}"
    echo ""
    echo "下一步操作:"
    echo "1. 如果没有 .env 文件，请复制 .env.example 并配置 API 信息"
    echo "2. 运行测试：python test_basic.py"
    echo "3. 运行快速示例：python quick_start.py"
    echo "4. 运行主程序：python main.py"
else
    echo -e "${RED}✗ 存在缺失文件，请检查上面的输出${NC}"
fi

echo ""
echo "=================================================="
