"""Stage74 v19 isolated PostgreSQL concurrency harness. Requires a dedicated EMPTY test database.
Install: python -m pip install 'psycopg[binary]>=3.2,<4'
Run: STAGE74_V19_TEST_DSN='postgresql://...' STAGE74_V19_ALLOW_ISOLATED=YES python dev/tests/stage74_v19_concurrency.py
NEVER point this at chat/chat2 or any database containing real users.
"""
import os, uuid, time
from concurrent.futures import ThreadPoolExecutor
import psycopg

dsn=os.environ.get("STAGE74_V19_TEST_DSN")
if not dsn or os.environ.get("STAGE74_V19_ALLOW_ISOLATED")!="YES":
    raise SystemExit("Dedicated test DSN and STAGE74_V19_ALLOW_ISOLATED=YES required")
def connect(): return psycopg.connect(dsn,autocommit=False)
with connect() as c:
    with c.cursor() as cur:
        cur.execute("select current_database()")
        db=cur.fetchone()[0]
        if not db.startswith("stage74_v19_"):
            raise SystemExit("Refusing database without stage74_v19_ prefix: "+db)
        cur.execute("select exists(select 1 from information_schema.tables where table_schema='auth' and table_name='users')")
        if cur.fetchone()[0]: raise SystemExit("Refusing database with auth.users")
        cur.execute("select exists(select 1 from information_schema.tables where table_schema='public' and table_name='mb_wallets')")
        if cur.fetchone()[0]: raise SystemExit("Refusing database with real wallet tables")
schema="stage74_v19_"+uuid.uuid4().hex[:12]
def reset():
    with connect() as c:
        with c.cursor() as cur:
            cur.execute(f"truncate {schema}.requests, {schema}.ledger")
            cur.execute(f"update {schema}.rooms set active=false")
            cur.execute(f"update {schema}.wallets set balance=500")
def rejoin(request_id, delay=0):
    with connect() as c:
        with c.cursor() as cur:
            cur.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))",("v19:"+request_id,))
            cur.execute(f"select charged from {schema}.requests where request_id=%s",(request_id,))
            old=cur.fetchone()
            if old is not None: return {"charged":old[0],"replayed":True}
            cur.execute(f"select active from {schema}.rooms where id=1 for update")
            active=cur.fetchone()[0]
            if delay: time.sleep(delay)
            if active:
                cur.execute(f"insert into {schema}.requests values (%s,false)",(request_id,))
                return {"charged":False,"already_active":True}
            cur.execute(f"select balance from {schema}.wallets where id=1 for update")
            balance=cur.fetchone()[0]
            if balance<100: raise RuntimeError("INSUFFICIENT_POINTS")
            cur.execute(f"update {schema}.wallets set balance=balance-100 where id=1")
            cur.execute(f"update {schema}.rooms set active=true where id=1")
            cur.execute(f"insert into {schema}.ledger(amount) values(-100)")
            cur.execute(f"insert into {schema}.requests values (%s,true)",(request_id,))
            return {"charged":True,"replayed":False}
def state():
    with connect() as c:
        with c.cursor() as cur:
            cur.execute(f"select balance from {schema}.wallets")
            balance=cur.fetchone()[0]
            cur.execute(f"select count(*),coalesce(sum(amount),0) from {schema}.ledger")
            count,total=cur.fetchone()
            cur.execute(f"select count(*) from {schema}.requests")
            requests=cur.fetchone()[0]
            return balance,count,total,requests
def race(ids):
    with ThreadPoolExecutor(max_workers=len(ids)) as pool:
        futures=[pool.submit(rejoin,x,0.2 if i==0 else 0) for i,x in enumerate(ids)]
        return [f.result(timeout=20) for f in futures]
try:
    with connect() as c:
        with c.cursor() as cur:
            cur.execute(f"create schema {schema}")
            cur.execute(f"create table {schema}.wallets(id integer primary key,balance integer not null check(balance>=0))")
            cur.execute(f"create table {schema}.rooms(id integer primary key,active boolean not null)")
            cur.execute(f"create table {schema}.requests(request_id text primary key,charged boolean not null)")
            cur.execute(f"create table {schema}.ledger(id bigint generated always as identity primary key,amount integer not null)")
            cur.execute(f"insert into {schema}.wallets values(1,500)")
            cur.execute(f"insert into {schema}.rooms values(1,false)")
    for name,ids in [("same_request",["same"]*10),("different_requests",[str(i) for i in range(10)])]:
        reset()
        results=race(ids)
        balance,count,total,requests=state()
        assert (balance,count,total)==(400,1,-100),(name,results,state())
        assert requests==(1 if name=="same_request" else 10),(name,requests)
        print("PASS",name,"balance",balance,"debits",count,"requests",requests)
    reset()
    first=rejoin("lost-response")
    assert first["charged"]
    replay=rejoin("lost-response")
    assert replay["replayed"] and replay["charged"]
    assert state()==(400,1,-100,1),state()
    print("PASS", "response_lost_recovery",state())
finally:
    with connect() as c:
        with c.cursor() as cur:
            cur.execute(f"drop schema if exists {schema} cascade")
print("PASS isolated schema cleanup")
