$ErrorActionPreference = "Stop"
$base = "http://127.0.0.1:8030"
function AH($t){ @{ Authorization = "Bearer $t" } }
$m = Invoke-RestMethod "$base/auth/login" -Method Post -ContentType "application/json" -Body (@{email="rifat@skillhub.dev";password="Mentor123"}|ConvertTo-Json)
"1. mentor login OK"
$title = "E2E Verify Course " + (Get-Random -Maximum 9999)
$body = @{title=$title;description="auto test";category="Tech";language="en";price=499;duration_hours=6;level="Beginner";tags="test"} | ConvertTo-Json
$c = Invoke-RestMethod "$base/courses" -Method Post -Headers (AH $m.token) -ContentType "application/json" -Body $body
"2. create course OK id=" + $c.id + " status=" + $c.status
$a = Invoke-RestMethod "$base/auth/login" -Method Post -ContentType "application/json" -Body (@{email="admin@skillhub.dev";password="Admin123"}|ConvertTo-Json)
"3. admin login OK"
$n = Invoke-RestMethod "$base/notifications" -Headers (AH $a.token)
$hit = $n.notifications | Where-Object { $_.message -like ("*" + $title + "*") } | Select-Object -First 1
if ($hit) { "4. admin NOTIFIED OK" } else { "4. !! NO NOTIFICATION" }
$p = Invoke-RestMethod "$base/admin/courses/pending" -Headers (AH $a.token)
$inQ = @($p.courses | Where-Object { $_.id -eq $c.id }).Count
"5. in pending queue: " + ($inQ -gt 0)
$ap = Invoke-RestMethod "$base/admin/courses/$($c.id)/status" -Method Put -Headers (AH $a.token) -ContentType "application/json" -Body (@{status="published";note="looks good"}|ConvertTo-Json)
"6. approve OK: " + $ap.message
$n2 = Invoke-RestMethod "$base/notifications" -Headers (AH $m.token)
$hit2 = $n2.notifications | Where-Object { $_.message -like ("*" + $title + "*") } | Select-Object -First 1
if ($hit2) { "7. mentor notified of review: " + $hit2.message } else { "7. !! mentor not notified" }
Invoke-RestMethod "$base/courses/$($c.id)" -Method Delete -Headers (AH $m.token) | Out-Null
"8. cleanup done"
"ALL STEPS DONE"