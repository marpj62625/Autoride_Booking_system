$et = $null
try {
    $et = New-Object -ComObject 'ET.Application'
    Write-Host 'ET.Application created successfully'
} catch {
    Write-Host "ET failed: $_"
}

if ($et) {
    try {
        $et.Visible = $false
        $wb = $et.Workbooks.Open('C:\Users\patri\Downloads\AutoRide_ANNUAL_Report_2026 (3).xlsx')
        $ws = $wb.Sheets.Item('Executive Summary')
        for ($r = 1; $r -le 10; $r++) {
            $rowObj = $ws.Rows.Item($r)
            Write-Host ("Row $r`: Height=" + $rowObj.RowHeight + ", Hidden=" + $rowObj.Hidden)
        }
        $wb.Close($false)
    } catch {
        Write-Host "Error opening: $_"
    } finally {
        $et.Quit()
    }
}
