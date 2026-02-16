async function api(path, method='GET', body){
  const opts = {method, headers:{'Content-Type':'application/json'}}
  if(body) opts.body = JSON.stringify(body)
  const res = await fetch('/api'+path, opts)
  return res.json()
}

function todayStr(){
  const d = new Date();
  return d.toISOString().slice(0,10)
}

document.addEventListener('DOMContentLoaded', ()=>{
  const form = document.getElementById('entryForm')
  const dateInput = document.getElementById('date')
  const desc = document.getElementById('description')
  const amt = document.getElementById('amount')
  const filter = document.getElementById('filterDate')
  const loadBtn = document.getElementById('loadBtn')
  const tbody = document.querySelector('#msgs tbody')
  const balanceEl = document.getElementById('balance')
  let currentPage = 1
  let currentPerPage = parseInt(document.getElementById('perPage')?.value || '50')
  let userRole = null

  dateInput.value = todayStr()
  filter.value = todayStr()

  form.addEventListener('submit', async (e)=>{
    e.preventDefault()
    const payload = {date: dateInput.value, description: desc.value, amount: parseFloat(amt.value||0)}
    await api('/messages', 'POST', payload)
    desc.value=''; amt.value='';
    loadFor(filter.value)
  })

  loadBtn.addEventListener('click', ()=> loadFor(filter.value))
  document.getElementById('loadMore').addEventListener('click', ()=> loadFor(filter.value, false))

  document.getElementById('exportBtn').addEventListener('click', async ()=>{
    const start = document.getElementById('startDate') ? document.getElementById('startDate').value : ''
    const end = document.getElementById('endDate') ? document.getElementById('endDate').value : ''
    let params = ''
    if(start && end) params = `?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`
    else {
      const date = filter.value
      if(date) params = '?date='+encodeURIComponent(date)
    }
    // client-side quick check for admin role
    if(userRole !== 'admin'){ alert('export requires admin role'); return }
    // trigger download; requires admin
    const res = await fetch('/api/export'+params)
    if(res.status === 401){ alert('login required to export CSV'); return }
    if(res.status === 403){ alert('forbidden: admin only'); return }
    const text = await res.text()
    const cd = res.headers.get('Content-Disposition') || 'messages.csv'
    const filename = (cd.match(/filename="?([^\"]+)"?/) || [null, 'messages.csv'])[1]
    const blob = new Blob([text], {type: 'text/csv'})
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url)
  })

  document.getElementById('monthBtn').addEventListener('click', async ()=>{
    const m = document.getElementById('monthPicker').value
    if(!m){ alert('pick a month'); return }
    const [year,month] = m.split('-')
    const fmt = document.getElementById('monthFormat') ? document.getElementById('monthFormat').value : 'json'
    const res = await fetch('/api/monthly?year='+year+'&month='+month+'&format='+fmt)
    const json = await res.json()
    const el = document.getElementById('monthlySummary')
    if(fmt === 'json'){
      let html = `<div><strong>Total for ${json.year}-${json.month}: ${parseFloat(json.total||0).toFixed(2)}</strong></div>`
      html += '<table style="margin-top:8px"><thead><tr><th>Date</th><th>Total</th></tr></thead><tbody>'
      for(const d of json.by_day){ html += `<tr><td>${d.date}</td><td>${parseFloat(d.total).toFixed(2)}</td></tr>` }
      html += '</tbody></table>'
      el.innerHTML = html
    } else {
      // if not json, response is a download handled by browser; show a message
      el.innerHTML = 'Download started (check browser downloads)'
    }
  })

  // auth
  document.getElementById('loginBtn').addEventListener('click', async ()=>{
    const username = document.getElementById('username').value
    const password = document.getElementById('password').value
    const res = await fetch('/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username,password})})
    const j = await res.json()
    if(res.ok){ document.getElementById('userInfo').textContent = 'Logged in as '+j.user + (j.role ? ' ('+j.role+')' : '') ; userRole = j.role } else { alert(j.error||'login failed') }
  })

  document.getElementById('logoutBtn').addEventListener('click', async ()=>{
    await fetch('/logout', {method:'POST'})
    document.getElementById('userInfo').textContent = ''
  })

  // register
  document.getElementById('regBtn').addEventListener('click', async ()=>{
    const u = document.getElementById('regUser').value
    const p = document.getElementById('regPass').value
    const e = document.getElementById('regEmail').value
    if(!u||!p){ alert('enter username and password'); return }
    const res = await fetch('/register', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:u,password:p,email:e})})
    const j = await res.json()
    if(res.ok){ alert('registered') } else { alert(j.error||'error') }
  })

  document.getElementById('resetReqBtn').addEventListener('click', async ()=>{
    const u = document.getElementById('resetUser').value
    if(!u){ alert('enter username'); return }
    const res = await fetch('/reset-request', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:u})})
    const j = await res.json()
    if(res.ok){ alert('reset token: '+j.token+' (expires '+j.expiry+')') } else { alert(j.error||'error') }
  })

  document.getElementById('resetBtn').addEventListener('click', async ()=>{
    const token = document.getElementById('resetToken').value
    const np = document.getElementById('resetNew').value
    if(!token||!np){ alert('token and new password required'); return }
    const res = await fetch('/reset', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({token, new_password: np})})
    const j = await res.json()
    if(res.ok){ alert('password reset') } else { alert(j.error||'error') }
  })

  async function loadFor(date, reset=true){
    if(reset){ currentPage = 1; tbody.innerHTML = '' }
    currentPerPage = parseInt(document.getElementById('perPage')?.value || currentPerPage)
    const res = await fetch('/api/messages?date='+encodeURIComponent(date)+'&page='+currentPage+'&per_page='+currentPerPage)
    const data = await res.json()
    const msgs = data.items || data
    for(const m of msgs){
      const tr = document.createElement('tr')
      tr.innerHTML = `<td>${m.id}</td><td>${m.date}</td><td>${m.description}</td><td>${parseFloat(m.amount).toFixed(2)}</td>`
      tbody.appendChild(tr)
    }
    const bal = await api('/balance?date='+encodeURIComponent(date))
    balanceEl.textContent = parseFloat(bal.total||0).toFixed(2)
    // advance page if there are more items
    const total = data.total || msgs.length
    if((currentPage*currentPerPage) < total) currentPage++
  }

  loadFor(filter.value)
})
