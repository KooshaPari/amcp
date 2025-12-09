# 🚀 SmartCP Local Deployment - START HERE

## ⚡ Quick Start (3 Commands)

```bash
# 1. Copy environment template
cp .env.local .env

# 2. Add your API keys to .env (optional but recommended)
# Edit .env and add:
#   OPENAI_API_KEY=sk-...
#   ANTHROPIC_API_KEY=sk-ant-...
#   VOYAGE_API_KEY=pa-...

# 3. Start everything
./scripts/start-local.sh
```

**🎉 Done!** All services running:
- **SmartCP MCP**: http://localhost:8000
- **Bifrost HTTP API**: http://localhost:8001/docs
- **Bifrost GraphQL**: http://localhost:8080/graphql
- **Bifrost ML**: http://localhost:8002

---

## ✅ Verify Everything Works

```bash
# Check all services healthy
./scripts/health-check.sh

# Run comprehensive tests
./scripts/test-deployment.sh
```

Expected output:
```
========================================
SmartCP Service Health Check
========================================

HTTP Services:
Checking SmartCP MCP Server... ✓ Healthy
Checking Bifrost HTTP API... ✓ Healthy
Checking Bifrost GraphQL... ✓ Healthy
Checking Bifrost ML Service... ✓ Healthy

Infrastructure Services:
Checking PostgreSQL... ✓ Reachable
Checking Redis... ✓ Reachable
Checking Qdrant... ✓ Healthy

========================================
All services are healthy! ✓
========================================
```

---

## 📊 What's Running?

| Service | URL | Purpose |
|---------|-----|---------|
| **SmartCP** | http://localhost:8000 | FastMCP server with tools |
| **Bifrost API** | http://localhost:8001/docs | HTTP API (Swagger UI) |
| **Bifrost GraphQL** | http://localhost:8080/graphql | GraphQL Playground |
| **Bifrost ML** | http://localhost:8002 | ML inference service |
| **PostgreSQL** | localhost:5432 | Primary database |
| **Redis** | localhost:6379 | Cache + queues |
| **Qdrant** | http://localhost:6333/dashboard | Vector database |

---

## 🔍 Test Each Service

### SmartCP MCP Server
```bash
# Health check
curl http://localhost:8000/health

# List tools
curl http://localhost:8000/tools
```

### Bifrost HTTP API
```bash
# Health check
curl http://localhost:8001/health

# View API docs
open http://localhost:8001/docs
```

### Bifrost GraphQL
```bash
# Health check
curl http://localhost:8080/health

# Open playground
open http://localhost:8080/graphql
```

### Bifrost ML Service
```bash
# Health check
curl http://localhost:8002/health

# List models
curl http://localhost:8002/models
```

---

## 📝 View Logs

```bash
# All services
./scripts/logs.sh all

# Specific service
./scripts/logs.sh smartcp
./scripts/logs.sh bifrost-api
./scripts/logs.sh bifrost-backend
./scripts/logs.sh postgres

# Last 100 lines
./scripts/logs.sh smartcp --tail=100
```

---

## 🛑 Stop Services

```bash
# Stop (keeps data)
./scripts/stop-local.sh

# Stop and remove all data (fresh start)
docker-compose -f docker-compose.local.yml down -v
```

---

## 🔧 Common Issues & Solutions

### Issue: Services won't start

**Solution:**
```bash
# Check Docker is running
docker info

# Check ports aren't in use
lsof -i :8000 :8001 :8080 :5432

# Clean and restart
docker-compose -f docker-compose.local.yml down -v
./scripts/start-local.sh
```

### Issue: Service shows as "Unhealthy"

**Solution:**
```bash
# View logs for errors
./scripts/logs.sh smartcp --tail=100

# Restart specific service
docker-compose -f docker-compose.local.yml restart smartcp
```

### Issue: "Cannot connect to Docker daemon"

**Solution:**
```bash
# Start Docker Desktop
open -a Docker

# Wait and verify
docker info
```

### Issue: Port already in use

**Solution:**
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in .env
echo "SMARTCP_PORT=8010" >> .env
```

---

## 📚 Documentation

- **Quick Reference**: [DEPLOYMENT_QUICKSTART.md](./DEPLOYMENT_QUICKSTART.md)
- **Complete Guide**: [LOCAL_DEPLOYMENT.md](./LOCAL_DEPLOYMENT.md)
- **Detailed Summary**: [DOCKER_DEPLOYMENT_COMPLETE.md](./DOCKER_DEPLOYMENT_COMPLETE.md)
- **File Listing**: [DEPLOYMENT_FILES_CREATED.txt](./DEPLOYMENT_FILES_CREATED.txt)

---

## 🎯 Next Steps

After successful deployment:

1. **Explore the APIs**
   - Open http://localhost:8001/docs (Swagger)
   - Open http://localhost:8080/graphql (GraphQL Playground)

2. **Test Features**
   ```bash
   # Make test requests
   curl http://localhost:8000/tools
   curl http://localhost:8001/health
   ```

3. **View Logs**
   ```bash
   ./scripts/logs.sh all
   ```

4. **Make Changes**
   - Edit Python code → changes auto-reload
   - Edit Go code → rebuild required
   ```bash
   docker-compose -f docker-compose.local.yml up -d --build bifrost-backend
   ```

5. **Run Tests**
   ```bash
   docker-compose -f docker-compose.local.yml exec smartcp pytest tests/
   ```

---

## 💡 Tips

**Faster rebuilds:**
```bash
# Only rebuild changed service
docker-compose -f docker-compose.local.yml up -d --build smartcp
```

**Reset everything:**
```bash
# Nuclear option - fresh start
docker-compose -f docker-compose.local.yml down -v --rmi all
./scripts/start-local.sh
```

**Check resource usage:**
```bash
# Monitor containers
docker stats

# Check disk space
docker system df
```

**Database access:**
```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.local.yml exec postgres \
  psql -U smartcp_user -d smartcp

# Run query
docker-compose -f docker-compose.local.yml exec postgres \
  psql -U smartcp_user -d smartcp -c "SELECT * FROM users LIMIT 10;"
```

**Redis access:**
```bash
# Connect to Redis
docker-compose -f docker-compose.local.yml exec redis redis-cli

# Check keys
docker-compose -f docker-compose.local.yml exec redis redis-cli KEYS "*"
```

---

## ✅ Success Checklist

Your deployment is successful when:

- [ ] `./scripts/start-local.sh` completes without errors
- [ ] `./scripts/health-check.sh` shows all services healthy
- [ ] Can access http://localhost:8000/health
- [ ] Can access http://localhost:8001/docs
- [ ] Can access http://localhost:8080/graphql
- [ ] `./scripts/test-deployment.sh` passes all tests
- [ ] Can view logs with `./scripts/logs.sh`

**All checked?** You're ready to develop! 🎉

---

## 🆘 Getting Help

1. **Check logs first**: `./scripts/logs.sh [service]`
2. **Run health check**: `./scripts/health-check.sh`
3. **Read documentation**: See files listed above
4. **Common issues**: Check troubleshooting section above

---

## 📦 What You Get

- ✅ **7 services** running in Docker
- ✅ **Automatic database migrations**
- ✅ **Health checks** for all services
- ✅ **Logging** via helper scripts
- ✅ **Testing** end-to-end
- ✅ **Documentation** comprehensive
- ✅ **One-command** startup/shutdown

**Total setup time:** 2-5 minutes
**Ready to develop:** Immediately

---

**🚀 START DEVELOPING NOW!**

Run this and you're good to go:
```bash
./scripts/start-local.sh && ./scripts/health-check.sh
```

Happy coding! 🎊
