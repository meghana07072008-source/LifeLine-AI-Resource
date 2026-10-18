
export default async (req) => {
    const headers = {
        "Content-Type": "application/json"
    };

    if (req.method === "OPTIONS") {
        return new Response(null, { status: 204 });
    }

    if (!["GET", "POST"].includes(req.method)) {
        return Response.json(
            { detail: "Method not allowed" },
            { status: 405, headers }
        );
    }

    const supabaseUrl = process.env.SUPABASE_URL;
    const secretKey = process.env.SUPABASE_SECRET_KEY;

    if (!supabaseUrl || !secretKey) {
        return Response.json(
            { detail: "Database configuration is missing" },
            { status: 500, headers }
        );
    }

    const dbHeaders = {
        "apikey": secretKey,
        "Authorization": `Bearer ${secretKey}`,
        "Content-Type": "application/json"
    };

    try {
        if (req.method === "GET") {
            return Response.json(
                { message: "LifeLine AI API is running" },
                { status: 200, headers }
            );
        }

        const body = await req.json();

        const allowedResources = [
            "Blood",
            "Medical Supplies",
            "Ambulance"
        ];

        const allowedUrgencies = [
            "Critical", "High", "Normal", "Low"
        ];

        const units = Number(body.units);
        const location = String(body.location || "").trim();

        if (
            !allowedResources.includes(body.resource) ||
            !Number.isInteger(units) ||
            units < 1 ||
            location.length < 2 ||
            location.length > 150 ||
            !allowedUrgencies.includes(body.urgency) ||
            (body.resource === "Blood" &&
                !["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
                    .includes(body.blood_group))
        ) {
            return Response.json(
                { detail: "Please check the request details." },
                { status: 400, headers }
            );
        }

        const record = {
            resource: body.resource,
            blood_group: body.resource === "Blood"
                ? body.blood_group
                : "N/A",
            units,
            location,
            urgency: body.urgency,
            status: "Pending"
        };

        const insertResponse = await fetch(
            `${supabaseUrl}/rest/v1/emergency_requests?select=*`,
            {
                method: "POST",
                headers: {
                    ...dbHeaders,
                    "Prefer": "return=representation"
                },
                body: JSON.stringify(record)
            }
        );

        const inserted = await insertResponse.json();

        if (!insertResponse.ok || !inserted.length) {
            console.error("Database insert failed:", inserted);
            return Response.json(
                { detail: "Could not save the request." },
                { status: 500, headers }
            );
        }

        const saved = inserted[0];
        const requestCode = `LL-${String(saved.id).padStart(4, "0")}`;

        const updateResponse = await fetch(
            `${supabaseUrl}/rest/v1/emergency_requests?id=eq.${saved.id}`,
            {
                method: "PATCH",
                headers: {
                    ...dbHeaders,
                    "Prefer": "return=minimal"
                },
                body: JSON.stringify({ request_code: requestCode })
            }
        );

        if (!updateResponse.ok) {
            console.error("Request code update failed:", await updateResponse.text());
            return Response.json(
                { detail: "Request saved, but its tracking code could not be assigned." },
                { status: 500, headers }
            );
        }

        return Response.json(
            {
                message: "Emergency request received successfully!",
                request: {
                    ...saved,
                    request_code: requestCode
                }
            },
            { status: 201, headers }
        );

    } catch (error) {
        console.error("Request function error:", error);
        return Response.json(
            { detail: "An unexpected error occurred." },
            { status: 500, headers }
        );
    }
};
