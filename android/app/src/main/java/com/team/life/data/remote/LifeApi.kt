package com.team.life.data.remote

import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

interface LifeApi {
    @POST("auth/login") suspend fun login(@Body request: LoginRequest): ApiEnvelope<TokenDto>
    @POST("auth/register") suspend fun register(@Body request: RegisterRequest): ApiEnvelope<TokenDto>
    @POST("auth/logout") suspend fun logout(@Body request: LogoutRequest): ApiEnvelope<Unit>
    @GET("users/me") suspend fun profile(): ApiEnvelope<UserProfileDto>
    @PATCH("users/me") suspend fun updateProfile(@Body request: UpdateProfileRequest): ApiEnvelope<UserProfileDto>
    @POST("users/me/password") suspend fun changePassword(@Body request: ChangePasswordRequest): ApiEnvelope<Unit>
    @GET("users/me/settings") suspend fun settings(): ApiEnvelope<UserSettingsDto>
    @PUT("users/me/settings") suspend fun updateSettings(@Body request: UpdateSettingsRequest): ApiEnvelope<UserSettingsDto>

    @GET("weather/current")
    suspend fun currentWeather(@Query("city_code") cityCode: String, @Query("city_name") cityName: String? = null): ApiEnvelope<CurrentWeatherDto>
    @GET("weather/forecast")
    suspend fun forecast(
        @Query("city_code") cityCode: String,
        @Query("days") days: Int = 7,
        @Query("city_name") cityName: String? = null,
    ): ApiEnvelope<ForecastDto>

    @GET("todos") suspend fun todos(@Query("page_size") pageSize: Int = 100): ApiEnvelope<PageDto<TodoDto>>
    @POST("todos") suspend fun createTodo(@Body request: CreateTodoRequest): ApiEnvelope<TodoDto>
    @PATCH("todos/{id}") suspend fun updateTodo(@Path("id") id: Long, @Body request: UpdateTodoRequest): ApiEnvelope<TodoDto>
    @DELETE("todos/{id}") suspend fun deleteTodo(@Path("id") id: Long, @Query("version") version: Int): ApiEnvelope<Unit>

    @GET("memos") suspend fun memos(@Query("page_size") pageSize: Int = 100): ApiEnvelope<PageDto<MemoDto>>
    @POST("memos") suspend fun createMemo(@Body request: CreateMemoRequest): ApiEnvelope<MemoDto>
    @PATCH("memos/{id}") suspend fun updateMemo(@Path("id") id: Long, @Body request: UpdateMemoRequest): ApiEnvelope<MemoDto>
    @DELETE("memos/{id}") suspend fun deleteMemo(@Path("id") id: Long, @Query("version") version: Int): ApiEnvelope<Unit>

    @GET("accounting/categories") suspend fun accountingCategories(): ApiEnvelope<AccountingCategoryListDto>
    @GET("accounting/records") suspend fun accountingRecords(@Query("page_size") pageSize: Int = 100): ApiEnvelope<PageDto<AccountingRecordDto>>
    @POST("accounting/records") suspend fun createAccounting(@Body request: CreateAccountingRequest): ApiEnvelope<AccountingRecordDto>
    @PATCH("accounting/records/{id}") suspend fun updateAccounting(
        @Path("id") id: Long,
        @Body request: UpdateAccountingRequest,
    ): ApiEnvelope<AccountingRecordDto>
    @DELETE("accounting/records/{id}") suspend fun deleteAccounting(
        @Path("id") id: Long,
        @Query("version") version: Int,
    ): ApiEnvelope<Unit>
    @GET("accounting/summary") suspend fun accountingSummary(
        @Query("start_date") startDate: String,
        @Query("end_date") endDate: String,
        @Query("group_by") groupBy: String = "category",
    ): ApiEnvelope<AccountingSummaryDto>

    @POST("checkins") suspend fun checkIn(@Body request: CheckInRequest): ApiEnvelope<CheckInDto>
    @GET("checkins/stats") suspend fun checkInStats(): ApiEnvelope<CheckInStatsDto>
    @GET("checkins/calendar") suspend fun checkInCalendar(@Query("year") year: Int, @Query("month") month: Int): ApiEnvelope<CheckInCalendarDto>
    @GET("points/balance") suspend fun points(): ApiEnvelope<PointsDto>
    @GET("points/transactions") suspend fun pointTransactions(
        @Query("page_size") pageSize: Int = 100,
    ): ApiEnvelope<PageDto<PointTransactionDto>>
    @GET("badges") suspend fun badges(): ApiEnvelope<BadgeListDto>

    @POST("sync/push") suspend fun push(@Body request: SyncPushRequest): ApiEnvelope<SyncPushDto>
    @GET("sync/pull") suspend fun pull(
        @Query("since") since: String,
        @Query("entity_types") entityTypes: String = "todo,memo,accounting",
        @Query("limit") limit: Int = 500,
    ): ApiEnvelope<SyncPullDto>
}

interface RefreshApi {
    @POST("auth/refresh") fun refresh(@Body request: RefreshRequest): Call<ApiEnvelope<RefreshTokenDto>>
}
