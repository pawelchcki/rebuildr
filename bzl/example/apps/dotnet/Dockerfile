# https://github.com/gothinkster/aspnetcore-realworld-example-app/blob/master/Dockerfile
# b04d12347fb0137f2cf96ea1be8ee689ea658374

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY . .
RUN dotnet run --project build/build.csproj -- publish

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base

WORKDIR /app
COPY --from=build /src/publish .
EXPOSE 8080

ENTRYPOINT ["dotnet", "Conduit.dll"]