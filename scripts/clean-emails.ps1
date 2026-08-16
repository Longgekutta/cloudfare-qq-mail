# 邮件文件夹清理脚本
# 保留最近30天的邮件，清理旧邮件以释放空间

param(
    [int]$DaysToKeep = 30,
    [switch]$DryRun = $false
)

Write-Host "🧹 邮件文件夹清理脚本" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

$EmailFolder = "received_emails"
$CutoffDate = (Get-Date).AddDays(-$DaysToKeep)

Write-Host "📁 目标文件夹: $EmailFolder" -ForegroundColor Yellow
Write-Host "📅 保留日期: $($CutoffDate.ToString('yyyy-MM-dd HH:mm:ss')) 之后的文件" -ForegroundColor Yellow
Write-Host "🔍 模式: $(if($DryRun) {'预览模式（不实际删除）'} else {'实际清理模式'})" -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $EmailFolder)) {
    Write-Host "❌ 邮件文件夹不存在: $EmailFolder" -ForegroundColor Red
    exit 1
}

# 获取所有文件
Write-Host "📊 分析文件..." -ForegroundColor Cyan
$AllFiles = Get-ChildItem $EmailFolder -Recurse -File
$TotalFiles = $AllFiles.Count
$TotalSize = ($AllFiles | Measure-Object -Property Length -Sum).Sum

Write-Host "📈 当前状态:" -ForegroundColor White
Write-Host "   总文件数: $TotalFiles" -ForegroundColor White
Write-Host "   总大小: $([math]::Round($TotalSize/1MB, 2)) MB" -ForegroundColor White
Write-Host ""

# 找出要删除的文件
$FilesToDelete = $AllFiles | Where-Object { $_.LastWriteTime -lt $CutoffDate }
$FilesToKeep = $AllFiles | Where-Object { $_.LastWriteTime -ge $CutoffDate }

$DeleteCount = $FilesToDelete.Count
$DeleteSize = ($FilesToDelete | Measure-Object -Property Length -Sum).Sum
$KeepCount = $FilesToKeep.Count
$KeepSize = ($FilesToKeep | Measure-Object -Property Length -Sum).Sum

Write-Host "🗑️ 清理统计:" -ForegroundColor Yellow
Write-Host "   将删除: $DeleteCount 个文件 ($([math]::Round($DeleteSize/1MB, 2)) MB)" -ForegroundColor Red
Write-Host "   将保留: $KeepCount 个文件 ($([math]::Round($KeepSize/1MB, 2)) MB)" -ForegroundColor Green
Write-Host "   节省空间: $([math]::Round($DeleteSize/1MB, 2)) MB" -ForegroundColor Cyan
Write-Host ""

if ($DeleteCount -eq 0) {
    Write-Host "✅ 没有需要清理的文件" -ForegroundColor Green
    exit 0
}

# 按文件类型分组显示
Write-Host "📋 删除文件类型分布:" -ForegroundColor White
$FilesToDelete | Group-Object Extension | Sort-Object Count -Descending | ForEach-Object {
    $ext = if($_.Name) { $_.Name } else { "(无扩展名)" }
    $size = ($_.Group | Measure-Object -Property Length -Sum).Sum
    Write-Host "   $ext : $($_.Count) 个文件 ($([math]::Round($size/1MB, 2)) MB)" -ForegroundColor Gray
}
Write-Host ""

if ($DryRun) {
    Write-Host "🔍 预览模式 - 显示将要删除的文件（前20个）:" -ForegroundColor Yellow
    $FilesToDelete | Select-Object -First 20 | ForEach-Object {
        Write-Host "   $($_.FullName) ($([math]::Round($_.Length/1KB, 2)) KB)" -ForegroundColor Gray
    }
    if ($DeleteCount -gt 20) {
        Write-Host "   ... 还有 $($DeleteCount - 20) 个文件" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "💡 要实际执行清理，请运行: .\clean-emails.ps1 -DaysToKeep $DaysToKeep" -ForegroundColor Cyan
} else {
    Write-Host "⚠️ 即将删除 $DeleteCount 个文件，释放 $([math]::Round($DeleteSize/1MB, 2)) MB 空间" -ForegroundColor Yellow
    $confirm = Read-Host "确认继续吗？(y/N)"
    
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        Write-Host ""
        Write-Host "🗑️ 开始清理..." -ForegroundColor Red
        
        $DeletedCount = 0
        $DeletedSize = 0
        
        foreach ($file in $FilesToDelete) {
            try {
                $fileSize = $file.Length
                Remove-Item $file.FullName -Force
                $DeletedCount++
                $DeletedSize += $fileSize
                
                if ($DeletedCount % 100 -eq 0) {
                    Write-Host "   已删除 $DeletedCount/$DeleteCount 个文件..." -ForegroundColor Gray
                }
            }
            catch {
                Write-Host "   ❌ 删除失败: $($file.FullName) - $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        Write-Host ""
        Write-Host "✅ 清理完成!" -ForegroundColor Green
        Write-Host "   删除了 $DeletedCount 个文件" -ForegroundColor Green
        Write-Host "   释放了 $([math]::Round($DeletedSize/1MB, 2)) MB 空间" -ForegroundColor Green
        
        # 清理空文件夹
        Write-Host ""
        Write-Host "🧹 清理空文件夹..." -ForegroundColor Cyan
        Get-ChildItem $EmailFolder -Recurse -Directory | Where-Object { 
            (Get-ChildItem $_.FullName -Recurse -File).Count -eq 0 
        } | Remove-Item -Recurse -Force
        
        Write-Host "✅ 空文件夹清理完成" -ForegroundColor Green
    } else {
        Write-Host "❌ 用户取消操作" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🎉 脚本执行完成" -ForegroundColor Green
