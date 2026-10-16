@echo off
chcp 65001 >nul
title Khoi chay Ứng dung Demo - Du an Big Data FPS Telemetry
cls
@echo off

echo ==================================================================================================================
echo TIEN ICH KHOI CHAY DEMO DASHBOARD
echo ==================================================================================================================
echo.
echo.

:: --------------------------------------------------------------------------------------------------------------------
:: KIEM TRA TRANG THAI DOCKER DESKTOP VA CONTAINER
:: --------------------------------------------------------------------------------------------------------------------
echo ------------------------------------------------------------------------------------------------------------------
echo [-] Dang kiem tra trang thai Container 'bigdata-fps-engine'...
echo.

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop chua duoc bat! Vui long mo Docker Desktop len truoc.
    echo.
    pause
    exit /b
)

docker ps -q --filter "name=bigdata-fps-engine" --filter "status=running" | findstr /r "." >nul 2>&1
if errorlevel 1 (
    echo [INFO] Container chua bat, dang tu dong khoi dong container...
    docker compose up -d
    echo.
)

echo [OK] Container 'bigdata-fps-engine' dang hoat dong on dinh.
echo.
echo.

:: --------------------------------------------------------------------------------------------------------------------
:: KHOI DONG SERVER STREAMLIT BEN TRONG CONTAINER
:: --------------------------------------------------------------------------------------------------------------------
echo ------------------------------------------------------------------------------------------------------------------
echo [-] Dang khoi chay ung dung Dashboard bang Streamlit...
echo [+] Cua so Web se tu dong mo tai dia chi: http://localhost:8501
echo.

:: Tu dong don dep tien trinh Streamlit cu tranh chiem cong 8501
docker exec bigdata-fps-engine pkill -9 -f streamlit >nul 2>&1
timeout /t 1 /nobreak >nul

:: Mo trinh duyet sau 3 giay de cho server khoi dong
start "" http://localhost:8501

echo [OK] Da kich hoat tien trinh Web Dashboard.
echo.
echo ------------------------------------------------------------------------------------------------------------------
echo THONG TIN TRUY CAP VA THEO DOI HE THONG:
echo  - Giao dien Web Demo: http://localhost:8501
echo  - Giam sat Apache Spark UI: http://localhost:4040
echo ------------------------------------------------------------------------------------------------------------------
echo.
echo (Nhan to hop phim Ctrl + C trong cua so nay neu muon dung chuong trinh)
echo.

docker exec -it bigdata-fps-engine streamlit run src/app.py --server.port 8501 --server.address 0.0.0.0

pause
