
\restrict nKCOMuq2zRy205tcVMz6adD3fBdPeSeBsNY4CvX75ddO4GZQz5wuKngRt0Iojjt


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE TYPE public.account_status AS ENUM (
    'Active',
    'Suspended',
    'Banned'
);


ALTER TYPE public.account_status OWNER TO postgres;


CREATE TYPE public.event_status AS ENUM (
    'Pending',
    'Confirmed',
    'Completed',
    'Cancelled'
);


ALTER TYPE public.event_status OWNER TO postgres;


CREATE TYPE public.payment_status AS ENUM (
    'Unpaid',
    'Pending',
    'Partial',
    'Paid',
    'Failed',
    'Refunded'
);


ALTER TYPE public.payment_status OWNER TO postgres;


CREATE TYPE public.role_enum AS ENUM (
    'Admin',
    'Organizer',
    'Customer'
);


ALTER TYPE public.role_enum OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;


CREATE TABLE public.admin_info (
    admin_id character varying(50) NOT NULL,
    access_level character varying(50) DEFAULT 'Support'::character varying
);


ALTER TABLE public.admin_info OWNER TO postgres;


CREATE TABLE public.chat_rooms (
    id character varying(50) NOT NULL,
    customer_id character varying(50),
    org_id character varying(50),
    event_id character varying(50)
);


ALTER TABLE public.chat_rooms OWNER TO postgres;


CREATE TABLE public.chatbot_interactions (
    id character varying(50) NOT NULL,
    customer_id character varying(50),
    query_text text NOT NULL,
    ai_response jsonb,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.chatbot_interactions OWNER TO postgres;


CREATE TABLE public.customer_info (
    customer_id character varying(50) NOT NULL,
    full_name character varying(100) NOT NULL,
    email character varying(100) NOT NULL,
    phone character varying(20),
    address text
);


ALTER TABLE public.customer_info OWNER TO postgres;


CREATE TABLE public.event_addon_selections (
    id character varying(50) NOT NULL,
    order_id character varying(50),
    addon_id character varying(50),
    unit_price numeric(10,2) NOT NULL
);


ALTER TABLE public.event_addon_selections OWNER TO postgres;


CREATE TABLE public.event_orders (
    id character varying(50) NOT NULL,
    event_id character varying(50),
    listing_id character varying(50),
    base_price_at_booking numeric(10,2) NOT NULL,
    total_addons_cost numeric(10,2) DEFAULT 0.00,
    final_total_price numeric(10,2) NOT NULL,
    payment_status public.payment_status DEFAULT 'Unpaid'::public.payment_status
);


ALTER TABLE public.event_orders OWNER TO postgres;


CREATE TABLE public.events (
    id character varying(50) NOT NULL,
    customer_id character varying(50),
    org_id character varying(50),
    event_date date NOT NULL,
    status public.event_status DEFAULT 'Pending'::public.event_status
);


ALTER TABLE public.events OWNER TO postgres;


CREATE TABLE public.financial_summaries (
    id character varying(50) NOT NULL,
    order_id character varying(50),
    total_revenue numeric(10,2) DEFAULT 0.00,
    total_cost numeric(10,2) DEFAULT 0.00,
    net_profit numeric(10,2) DEFAULT 0.00
);


ALTER TABLE public.financial_summaries OWNER TO postgres;


CREATE TABLE public.listing_images (
    id character varying(50) NOT NULL,
    listing_id character varying(50),
    image_url text NOT NULL
);


ALTER TABLE public.listing_images OWNER TO postgres;


CREATE TABLE public.messages (
    id character varying(50) NOT NULL,
    room_id character varying(50),
    sender_id character varying(50),
    message_text text,
    image_url text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.messages OWNER TO postgres;


CREATE TABLE public.organizer_info (
    org_id character varying(50) NOT NULL,
    company_name character varying(100) NOT NULL,
    email character varying(100) NOT NULL,
    primary_category character varying(50),
    is_verified boolean DEFAULT false
);


ALTER TABLE public.organizer_info OWNER TO postgres;


CREATE TABLE public.payment_milestones (
    id character varying(50) NOT NULL,
    order_id character varying(50),
    amount numeric(10,2) NOT NULL,
    due_date date NOT NULL,
    status public.payment_status DEFAULT 'Unpaid'::public.payment_status
);


ALTER TABLE public.payment_milestones OWNER TO postgres;


CREATE TABLE public.service_addons (
    id character varying(50) NOT NULL,
    listing_id character varying(50),
    addon_name character varying(100) NOT NULL,
    price numeric(10,2) NOT NULL
);


ALTER TABLE public.service_addons OWNER TO postgres;


CREATE TABLE public.service_listings (
    id character varying(50) NOT NULL,
    org_id character varying(50),
    category character varying(50) NOT NULL,
    title character varying(150) NOT NULL,
    base_price numeric(10,2) NOT NULL
);


ALTER TABLE public.service_listings OWNER TO postgres;


CREATE TABLE public.transaction_log (
    id character varying(50) NOT NULL,
    order_id character varying(50),
    user_id character varying(50),
    org_id character varying(50),
    gateway_ref character varying(100),
    amount numeric(10,2) NOT NULL,
    status public.payment_status NOT NULL,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.transaction_log OWNER TO postgres;


CREATE TABLE public.user_main (
    id character varying(50) NOT NULL,
    username character varying(50) NOT NULL,
    password character varying(255) NOT NULL,
    role public.role_enum NOT NULL
);


ALTER TABLE public.user_main OWNER TO postgres;


CREATE TABLE public.user_status (
    user_id character varying(50) NOT NULL,
    status public.account_status DEFAULT 'Active'::public.account_status,
    reason text,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_status OWNER TO postgres;


CREATE TABLE public.vendor_analytics (
    org_id character varying(50) NOT NULL,
    total_events integer DEFAULT 0,
    total_earnings numeric(10,2) DEFAULT 0.00
);


ALTER TABLE public.vendor_analytics OWNER TO postgres;


CREATE TABLE public.vendor_reviews (
    id character varying(50) NOT NULL,
    event_id character varying(50),
    vendor_id character varying(50),
    rating integer,
    comment text,
    CONSTRAINT vendor_reviews_rating_check CHECK (((rating >= 1) AND (rating <= 5)))
);


ALTER TABLE public.vendor_reviews OWNER TO postgres;


COPY public.admin_info (admin_id, access_level) FROM stdin;
\.



COPY public.chat_rooms (id, customer_id, org_id, event_id) FROM stdin;
ROOM-01	CUST-01	ORG-01	EVT-01
ROOM-02	CUST-02	ORG-02	EVT-02
\.



COPY public.chatbot_interactions (id, customer_id, query_text, ai_response, "timestamp") FROM stdin;
CHAT-01	CUST-01	I need a full wedding planner under 6000	{"budget_match": true, "suggested_categories": ["Full Event Planner"]}	2026-04-12 23:36:47.558737
CHAT-02	CUST-02	Loud speakers for an outdoor party	{"budget_match": true, "suggested_categories": ["Sound & Lighting"]}	2026-04-12 23:36:47.558737
\.



COPY public.customer_info (customer_id, full_name, email, phone, address) FROM stdin;
CUST-01	Alice Smith	alice@email.com	1234567890	123 Apple St
CUST-02	Bob Jones	bob@email.com	0987654321	456 Banana Ave
CUST-03	Charlie Brown	charlie@email.com	5556667777	789 Cherry Blvd
\.



COPY public.event_addon_selections (id, order_id, addon_id, unit_price) FROM stdin;
SEL-01	ORD-01	ADD-01	500.00
SEL-02	ORD-02	ADD-03	100.00
\.



COPY public.event_orders (id, event_id, listing_id, base_price_at_booking, total_addons_cost, final_total_price, payment_status) FROM stdin;
ORD-01	EVT-01	LIST-01	5000.00	500.00	5500.00	Partial
ORD-02	EVT-02	LIST-02	1500.00	100.00	1600.00	Paid
ORD-03	EVT-03	LIST-03	2000.00	0.00	2000.00	Unpaid
\.



COPY public.events (id, customer_id, org_id, event_date, status) FROM stdin;
EVT-01	CUST-01	ORG-01	2026-06-15	Confirmed
EVT-02	CUST-02	ORG-02	2026-07-20	Confirmed
EVT-03	CUST-03	ORG-03	2026-08-10	Pending
\.



COPY public.financial_summaries (id, order_id, total_revenue, total_cost, net_profit) FROM stdin;
FIN-01	ORD-01	5500.00	5000.00	500.00
FIN-02	ORD-02	1600.00	1400.00	200.00
FIN-03	ORD-03	2000.00	1800.00	200.00
\.



COPY public.listing_images (id, listing_id, image_url) FROM stdin;
IMG-01	LIST-01	null.jpg
IMG-02	LIST-02	null.jpg
IMG-03	LIST-03	null.jpg
\.



COPY public.messages (id, room_id, sender_id, message_text, image_url, "timestamp") FROM stdin;
MSG-01	ROOM-01	CUST-01	Hi, does the premium package include flowers?	null.jpg	2026-04-12 23:36:47.563662
MSG-02	ROOM-01	ORG-01	Yes, basic floral is included! You can add extra if needed.	null.jpg	2026-04-12 23:36:47.563662
MSG-03	ROOM-02	CUST-02	Is the smoke machine safe for outdoors?	null.jpg	2026-04-12 23:36:47.563662
\.



COPY public.organizer_info (org_id, company_name, email, primary_category, is_verified) FROM stdin;
ORG-01	Dream Events	contact@dreamevents.com	Full Event Planner	t
ORG-02	Sound Masters	info@soundmasters.com	Sound & Lighting	t
ORG-03	Taste Catering	hello@tastecatering.com	Catering	f
\.



COPY public.payment_milestones (id, order_id, amount, due_date, status) FROM stdin;
MILE-01	ORD-01	2750.00	2026-05-01	Paid
MILE-02	ORD-01	2750.00	2026-06-10	Unpaid
MILE-03	ORD-02	1600.00	2026-07-01	Paid
MILE-04	ORD-03	2000.00	2026-08-01	Unpaid
\.



COPY public.service_addons (id, listing_id, addon_name, price) FROM stdin;
ADD-01	LIST-01	Drone Photography	500.00
ADD-02	LIST-01	Extra Floral Decor	300.00
ADD-03	LIST-02	Smoke Machine	100.00
ADD-04	LIST-03	Premium Dessert Bar	250.00
\.



COPY public.service_listings (id, org_id, category, title, base_price) FROM stdin;
LIST-01	ORG-01	Full Event Planner	Premium Wedding Package	5000.00
LIST-02	ORG-02	Sound & Lighting	Concert Audio Setup	1500.00
LIST-03	ORG-03	Catering	Corporate Buffet Dinner	2000.00
\.



COPY public.transaction_log (id, order_id, user_id, org_id, gateway_ref, amount, status, "timestamp") FROM stdin;
TXN-01	ORD-01	CUST-01	ORG-01	TXN_99887766	2750.00	Paid	2026-04-12 23:36:47.554124
TXN-02	ORD-02	CUST-02	ORG-02	TXN_55443322	1600.00	Paid	2026-04-12 23:36:47.554124
\.



COPY public.user_main (id, username, password, role) FROM stdin;
CUST-01	alice_cust	hash123	Customer
CUST-02	bob_cust	hash123	Customer
CUST-03	charlie_cust	hash123	Customer
ORG-01	dream_events	hash123	Organizer
ORG-02	sound_masters	hash123	Organizer
ORG-03	taste_catering	hash123	Organizer
\.



COPY public.user_status (user_id, status, reason, updated_at) FROM stdin;
CUST-01	Active	New registration	2026-04-12 23:36:47.534906
CUST-02	Active	New registration	2026-04-12 23:36:47.534906
CUST-03	Active	New registration	2026-04-12 23:36:47.534906
ORG-01	Active	New registration	2026-04-12 23:36:47.534906
ORG-02	Active	New registration	2026-04-12 23:36:47.534906
ORG-03	Active	New registration	2026-04-12 23:36:47.534906
\.



COPY public.vendor_analytics (org_id, total_events, total_earnings) FROM stdin;
ORG-01	10	45000.00
ORG-02	5	7500.00
ORG-03	2	4000.00
\.



COPY public.vendor_reviews (id, event_id, vendor_id, rating, comment) FROM stdin;
REV-01	EVT-01	ORG-01	5	Absolutely fantastic planning!
REV-02	EVT-02	ORG-02	4	Great sound, but arrived a bit late.
\.



ALTER TABLE ONLY public.admin_info
    ADD CONSTRAINT admin_info_pkey PRIMARY KEY (admin_id);



ALTER TABLE ONLY public.chat_rooms
    ADD CONSTRAINT chat_rooms_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.chatbot_interactions
    ADD CONSTRAINT chatbot_interactions_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.customer_info
    ADD CONSTRAINT customer_info_email_key UNIQUE (email);



ALTER TABLE ONLY public.customer_info
    ADD CONSTRAINT customer_info_pkey PRIMARY KEY (customer_id);



ALTER TABLE ONLY public.event_addon_selections
    ADD CONSTRAINT event_addon_selections_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.event_orders
    ADD CONSTRAINT event_orders_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.financial_summaries
    ADD CONSTRAINT financial_summaries_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.listing_images
    ADD CONSTRAINT listing_images_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.organizer_info
    ADD CONSTRAINT organizer_info_email_key UNIQUE (email);



ALTER TABLE ONLY public.organizer_info
    ADD CONSTRAINT organizer_info_pkey PRIMARY KEY (org_id);



ALTER TABLE ONLY public.payment_milestones
    ADD CONSTRAINT payment_milestones_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.service_addons
    ADD CONSTRAINT service_addons_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.service_listings
    ADD CONSTRAINT service_listings_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.transaction_log
    ADD CONSTRAINT transaction_log_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.user_main
    ADD CONSTRAINT user_main_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.user_main
    ADD CONSTRAINT user_main_username_key UNIQUE (username);



ALTER TABLE ONLY public.user_status
    ADD CONSTRAINT user_status_pkey PRIMARY KEY (user_id);



ALTER TABLE ONLY public.vendor_analytics
    ADD CONSTRAINT vendor_analytics_pkey PRIMARY KEY (org_id);



ALTER TABLE ONLY public.vendor_reviews
    ADD CONSTRAINT vendor_reviews_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.admin_info
    ADD CONSTRAINT admin_info_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES public.user_main(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.chat_rooms
    ADD CONSTRAINT chat_rooms_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customer_info(customer_id);



ALTER TABLE ONLY public.chat_rooms
    ADD CONSTRAINT chat_rooms_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.chat_rooms
    ADD CONSTRAINT chat_rooms_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizer_info(org_id);



ALTER TABLE ONLY public.chatbot_interactions
    ADD CONSTRAINT chatbot_interactions_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customer_info(customer_id) ON DELETE CASCADE;



ALTER TABLE ONLY public.customer_info
    ADD CONSTRAINT customer_info_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.user_main(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.event_addon_selections
    ADD CONSTRAINT event_addon_selections_addon_id_fkey FOREIGN KEY (addon_id) REFERENCES public.service_addons(id);



ALTER TABLE ONLY public.event_addon_selections
    ADD CONSTRAINT event_addon_selections_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.event_orders(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.event_orders
    ADD CONSTRAINT event_orders_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.event_orders
    ADD CONSTRAINT event_orders_listing_id_fkey FOREIGN KEY (listing_id) REFERENCES public.service_listings(id);



ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customer_info(customer_id);



ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizer_info(org_id);



ALTER TABLE ONLY public.financial_summaries
    ADD CONSTRAINT financial_summaries_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.event_orders(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.listing_images
    ADD CONSTRAINT listing_images_listing_id_fkey FOREIGN KEY (listing_id) REFERENCES public.service_listings(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_room_id_fkey FOREIGN KEY (room_id) REFERENCES public.chat_rooms(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.user_main(id);



ALTER TABLE ONLY public.organizer_info
    ADD CONSTRAINT organizer_info_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.user_main(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.payment_milestones
    ADD CONSTRAINT payment_milestones_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.event_orders(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.service_addons
    ADD CONSTRAINT service_addons_listing_id_fkey FOREIGN KEY (listing_id) REFERENCES public.service_listings(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.service_listings
    ADD CONSTRAINT service_listings_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizer_info(org_id) ON DELETE CASCADE;



ALTER TABLE ONLY public.transaction_log
    ADD CONSTRAINT transaction_log_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.event_orders(id) ON DELETE SET NULL;



ALTER TABLE ONLY public.transaction_log
    ADD CONSTRAINT transaction_log_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizer_info(org_id);



ALTER TABLE ONLY public.transaction_log
    ADD CONSTRAINT transaction_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_main(id);



ALTER TABLE ONLY public.user_status
    ADD CONSTRAINT user_status_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_main(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.vendor_analytics
    ADD CONSTRAINT vendor_analytics_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizer_info(org_id) ON DELETE CASCADE;



ALTER TABLE ONLY public.vendor_reviews
    ADD CONSTRAINT vendor_reviews_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.vendor_reviews
    ADD CONSTRAINT vendor_reviews_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.organizer_info(org_id);



\unrestrict nKCOMuq2zRy205tcVMz6adD3fBdPeSeBsNY4CvX75ddO4GZQz5wuKngRt0Iojjt

