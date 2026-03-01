--
-- PostgreSQL database dump
--

\restrict 3Hhl5eXrSZAK6x0qzWVFGhbXy0e2GGYvG95AUyKgAKut6g19etqyDC4yZTmuJAz

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO oliver;

--
-- Name: daily_notes; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.daily_notes (
    id integer NOT NULL,
    day_id integer NOT NULL,
    content text DEFAULT ''::text NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.daily_notes OWNER TO oliver;

--
-- Name: daily_notes_id_seq; Type: SEQUENCE; Schema: public; Owner: oliver
--

CREATE SEQUENCE public.daily_notes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.daily_notes_id_seq OWNER TO oliver;

--
-- Name: daily_notes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oliver
--

ALTER SEQUENCE public.daily_notes_id_seq OWNED BY public.daily_notes.id;


--
-- Name: day_metadata; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.day_metadata (
    id integer NOT NULL,
    day_id integer NOT NULL,
    temperature_c double precision,
    condition character varying(50),
    moon_phase character varying(50)
);


ALTER TABLE public.day_metadata OWNER TO oliver;

--
-- Name: day_metadata_id_seq; Type: SEQUENCE; Schema: public; Owner: oliver
--

CREATE SEQUENCE public.day_metadata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.day_metadata_id_seq OWNER TO oliver;

--
-- Name: day_metadata_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oliver
--

ALTER SEQUENCE public.day_metadata_id_seq OWNED BY public.day_metadata.id;


--
-- Name: day_offs; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.day_offs (
    id integer NOT NULL,
    day_id integer NOT NULL,
    reason character varying(50) NOT NULL,
    note text
);


ALTER TABLE public.day_offs OWNER TO oliver;

--
-- Name: day_offs_id_seq; Type: SEQUENCE; Schema: public; Owner: oliver
--

CREATE SEQUENCE public.day_offs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.day_offs_id_seq OWNER TO oliver;

--
-- Name: day_offs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oliver
--

ALTER SEQUENCE public.day_offs_id_seq OWNED BY public.day_offs.id;


--
-- Name: day_ratings; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.day_ratings (
    id integer NOT NULL,
    day_id integer NOT NULL,
    focus integer,
    energy integer,
    satisfaction integer
);


ALTER TABLE public.day_ratings OWNER TO oliver;

--
-- Name: day_ratings_id_seq; Type: SEQUENCE; Schema: public; Owner: oliver
--

CREATE SEQUENCE public.day_ratings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.day_ratings_id_seq OWNER TO oliver;

--
-- Name: day_ratings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oliver
--

ALTER SEQUENCE public.day_ratings_id_seq OWNED BY public.day_ratings.id;


--
-- Name: days; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.days (
    id integer NOT NULL,
    date date NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.days OWNER TO oliver;

--
-- Name: days_id_seq; Type: SEQUENCE; Schema: public; Owner: oliver
--

CREATE SEQUENCE public.days_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.days_id_seq OWNER TO oliver;

--
-- Name: days_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oliver
--

ALTER SEQUENCE public.days_id_seq OWNED BY public.days.id;


--
-- Name: goal_tags; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.goal_tags (
    goal_id integer NOT NULL,
    tag_id integer NOT NULL
);


ALTER TABLE public.goal_tags OWNER TO oliver;

--
-- Name: goal_tasks; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.goal_tasks (
    goal_id integer NOT NULL,
    task_id integer NOT NULL
);


ALTER TABLE public.goal_tasks OWNER TO oliver;

--
-- Name: goals; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.goals (
    id integer NOT NULL,
    title character varying NOT NULL,
    description character varying,
    target_date date,
    status character varying NOT NULL,
    completed_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.goals OWNER TO oliver;

--
-- Name: goals_id_seq; Type: SEQUENCE; Schema: public; Owner: oliver
--

CREATE SEQUENCE public.goals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.goals_id_seq OWNER TO oliver;

--
-- Name: goals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oliver
--

ALTER SEQUENCE public.goals_id_seq OWNED BY public.goals.id;


--
-- Name: reminders; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.reminders (
    id integer NOT NULL,
    task_id integer NOT NULL,
    remind_at timestamp with time zone NOT NULL,
    message character varying NOT NULL,
    is_delivered boolean NOT NULL
);


ALTER TABLE public.reminders OWNER TO oliver;

--
-- Name: reminders_id_seq; Type: SEQUENCE; Schema: public; Owner: oliver
--

CREATE SEQUENCE public.reminders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reminders_id_seq OWNER TO oliver;

--
-- Name: reminders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oliver
--

ALTER SEQUENCE public.reminders_id_seq OWNED BY public.reminders.id;


--
-- Name: roadblocks; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.roadblocks (
    id integer NOT NULL,
    day_id integer NOT NULL,
    content text DEFAULT ''::text NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.roadblocks OWNER TO oliver;

--
-- Name: roadblocks_id_seq; Type: SEQUENCE; Schema: public; Owner: oliver
--

CREATE SEQUENCE public.roadblocks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roadblocks_id_seq OWNER TO oliver;

--
-- Name: roadblocks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oliver
--

ALTER SEQUENCE public.roadblocks_id_seq OWNED BY public.roadblocks.id;


--
-- Name: settings; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.settings (
    key character varying NOT NULL,
    value character varying NOT NULL
);


ALTER TABLE public.settings OWNER TO oliver;

--
-- Name: tags; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.tags (
    id integer NOT NULL,
    name character varying NOT NULL
);


ALTER TABLE public.tags OWNER TO oliver;

--
-- Name: tags_id_seq; Type: SEQUENCE; Schema: public; Owner: oliver
--

CREATE SEQUENCE public.tags_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tags_id_seq OWNER TO oliver;

--
-- Name: tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oliver
--

ALTER SEQUENCE public.tags_id_seq OWNED BY public.tags.id;


--
-- Name: task_tags; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.task_tags (
    task_id integer NOT NULL,
    tag_id integer NOT NULL
);


ALTER TABLE public.task_tags OWNER TO oliver;

--
-- Name: task_templates; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.task_templates (
    id integer NOT NULL,
    title character varying NOT NULL,
    description character varying,
    category character varying,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.task_templates OWNER TO oliver;

--
-- Name: task_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: oliver
--

CREATE SEQUENCE public.task_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.task_templates_id_seq OWNER TO oliver;

--
-- Name: task_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oliver
--

ALTER SEQUENCE public.task_templates_id_seq OWNED BY public.task_templates.id;


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.tasks (
    id integer NOT NULL,
    day_id integer,
    category character varying,
    title character varying NOT NULL,
    description character varying,
    status character varying NOT NULL,
    order_index integer NOT NULL,
    completed_at timestamp with time zone
);


ALTER TABLE public.tasks OWNER TO oliver;

--
-- Name: tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: oliver
--

CREATE SEQUENCE public.tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tasks_id_seq OWNER TO oliver;

--
-- Name: tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oliver
--

ALTER SEQUENCE public.tasks_id_seq OWNED BY public.tasks.id;


--
-- Name: template_schedules; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.template_schedules (
    id integer NOT NULL,
    template_id integer NOT NULL,
    recurrence character varying(20) NOT NULL,
    anchor_date date NOT NULL,
    next_run_date date NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.template_schedules OWNER TO oliver;

--
-- Name: template_schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: oliver
--

CREATE SEQUENCE public.template_schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.template_schedules_id_seq OWNER TO oliver;

--
-- Name: template_schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oliver
--

ALTER SEQUENCE public.template_schedules_id_seq OWNED BY public.template_schedules.id;


--
-- Name: template_tags; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.template_tags (
    template_id integer NOT NULL,
    tag_id integer NOT NULL
);


ALTER TABLE public.template_tags OWNER TO oliver;

--
-- Name: timer_sessions; Type: TABLE; Schema: public; Owner: oliver
--

CREATE TABLE public.timer_sessions (
    id integer NOT NULL,
    task_id integer NOT NULL,
    started_at timestamp with time zone NOT NULL,
    ended_at timestamp with time zone,
    duration_seconds integer
);


ALTER TABLE public.timer_sessions OWNER TO oliver;

--
-- Name: timer_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: oliver
--

CREATE SEQUENCE public.timer_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.timer_sessions_id_seq OWNER TO oliver;

--
-- Name: timer_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oliver
--

ALTER SEQUENCE public.timer_sessions_id_seq OWNED BY public.timer_sessions.id;


--
-- Name: daily_notes id; Type: DEFAULT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.daily_notes ALTER COLUMN id SET DEFAULT nextval('public.daily_notes_id_seq'::regclass);


--
-- Name: day_metadata id; Type: DEFAULT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.day_metadata ALTER COLUMN id SET DEFAULT nextval('public.day_metadata_id_seq'::regclass);


--
-- Name: day_offs id; Type: DEFAULT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.day_offs ALTER COLUMN id SET DEFAULT nextval('public.day_offs_id_seq'::regclass);


--
-- Name: day_ratings id; Type: DEFAULT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.day_ratings ALTER COLUMN id SET DEFAULT nextval('public.day_ratings_id_seq'::regclass);


--
-- Name: days id; Type: DEFAULT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.days ALTER COLUMN id SET DEFAULT nextval('public.days_id_seq'::regclass);


--
-- Name: goals id; Type: DEFAULT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.goals ALTER COLUMN id SET DEFAULT nextval('public.goals_id_seq'::regclass);


--
-- Name: reminders id; Type: DEFAULT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.reminders ALTER COLUMN id SET DEFAULT nextval('public.reminders_id_seq'::regclass);


--
-- Name: roadblocks id; Type: DEFAULT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.roadblocks ALTER COLUMN id SET DEFAULT nextval('public.roadblocks_id_seq'::regclass);


--
-- Name: tags id; Type: DEFAULT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.tags ALTER COLUMN id SET DEFAULT nextval('public.tags_id_seq'::regclass);


--
-- Name: task_templates id; Type: DEFAULT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.task_templates ALTER COLUMN id SET DEFAULT nextval('public.task_templates_id_seq'::regclass);


--
-- Name: tasks id; Type: DEFAULT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.tasks ALTER COLUMN id SET DEFAULT nextval('public.tasks_id_seq'::regclass);


--
-- Name: template_schedules id; Type: DEFAULT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.template_schedules ALTER COLUMN id SET DEFAULT nextval('public.template_schedules_id_seq'::regclass);


--
-- Name: timer_sessions id; Type: DEFAULT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.timer_sessions ALTER COLUMN id SET DEFAULT nextval('public.timer_sessions_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.alembic_version (version_num) FROM stdin;
2ba492a38cff
\.


--
-- Data for Name: daily_notes; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.daily_notes (id, day_id, content, updated_at) FROM stdin;
1	14	Great end to the first sprint. PR merged, CI green, v0.3-rc1 announced on dev.to. Got a warm response from the community. Long trail walk with Mochi and Biscuit to close out the week — both very happy about it.	2026-03-01 17:17:41.191228+00
2	10	Fresh start to the sprint. Spent the morning planning out the async architecture — really happy with how the tokio::fs design came together. Nine issues triaged before lunch. Good energy this week.	2026-03-01 17:17:41.192853+00
3	12	The race condition in the async watcher tests took most of the afternoon. It only shows up under rapid successive writes — turned out to be a dropped event when two changes hit within ~5ms. Reproduced reliably with a sleep in tests and fixed it, but reminded me why concurrent code needs careful design from the start.	2026-03-01 17:17:41.193613+00
5	13	Rainy all day — perfect conditions for deep work. Knocked out the --dry-run flag, progress bar, and baseline benchmarks. Biscuit at the groomer so the house was unusually quiet. Very productive day overall.	2026-03-01 17:17:41.195685+00
6	19	Back with clear goals after a restful weekend. The KeepLatest strategy came together quicker than expected — cleaner implementation than I'd imagined. Proptest is fantastic for this kind of state machine logic. Good week ahead.	2026-03-01 17:17:41.275612+00
7	23	v0.4-alpha is out. The telemetry module took longer than expected but the privacy controls feel right — explicit opt-in with a clear data description. Good community response to the announcement. Closed the week with a long sunny trail walk with Mochi and Biscuit. Really satisfying week.	2026-03-01 17:17:41.27593+00
9	21	Rainy all day, stayed deep in performance work. Found an unexpected allocation hotspot in the event deduplication loop — was cloning a Vec unnecessarily on every iteration. Fixed it and benchmark dropped from 12ms to 4ms per sync cycle. Dogs were restless with no outdoor time but we had a good indoor play session after lunch.	2026-03-01 17:17:41.276918+00
10	16	SHIPPED IT. treesync v0.3 live on crates.io. The docs came together really nicely and the awesome-rust submission is pending review. Mochi's vet checkup went perfectly — clean bill of health. Honestly one of the best workdays in a long time.	2026-03-01 17:18:51.563944+00
11	15	Diving into the vex codebase. It's larger and more complex than I expected — spent the whole morning just reading code before touching anything. By afternoon I had a solid mental model and the fix approach is clear. Slower start than hoped but the right call.	2026-03-01 17:18:51.566952+00
4	20	Cross-platform CI work turned out to be more involved than expected — Windows runner kept timing out on the file watcher tests. Took most of the morning to diagnose (different event ordering guarantees on NTFS). Got it green by EOD.	2026-03-01 17:18:51.568075+00
8	18	Foggy morning, took a while to get going. But once I was in the zone the v0.4 RFC practically wrote itself — the conflict resolution design feels solid. Excited to see what the community thinks. Riverside walk with the dogs in the afternoon cleared my head nicely.	2026-03-01 17:18:51.58904+00
12	22	Prepping for the v0.4-alpha announcement. Had to stop mid-afternoon to deal with treesync#234 (potential data loss on interrupted sync) — turned out to be user error, but the error message was genuinely misleading. Fixed the messaging and added a warning to the docs. Evening yoga was very much needed.	2026-03-01 17:19:13.320576+00
\.


--
-- Data for Name: day_metadata; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.day_metadata (id, day_id, temperature_c, condition, moon_phase) FROM stdin;
1	10	12	sunny	waxing_crescent
2	11	9	partly_cloudy	waxing_crescent
3	12	7	cloudy	first_quarter
4	13	6	rainy	first_quarter
5	14	14	sunny	waxing_gibbous
6	15	8	cloudy	waxing_gibbous
7	9	10	partly_cloudy	waxing_gibbous
8	16	15	sunny	full_moon
9	17	11	partly_cloudy	waning_gibbous
10	18	9	foggy	waning_gibbous
11	19	13	sunny	last_quarter
12	20	7	cloudy	last_quarter
13	21	5	rainy	waning_crescent
14	22	10	partly_cloudy	waning_crescent
15	23	16	sunny	new_moon
\.


--
-- Data for Name: day_offs; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.day_offs (id, day_id, reason, note) FROM stdin;
\.


--
-- Data for Name: day_ratings; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.day_ratings (id, day_id, focus, energy, satisfaction) FROM stdin;
1	13	4	4	4
2	18	3	3	4
3	15	3	3	3
4	12	5	3	3
5	14	4	4	5
6	11	4	3	4
7	20	4	3	3
8	16	5	5	5
9	9	4	4	4
10	19	5	4	4
11	10	4	4	4
12	17	3	4	4
13	23	4	5	5
14	22	4	4	4
15	21	5	4	4
\.


--
-- Data for Name: days; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.days (id, date, created_at) FROM stdin;
1	2026-03-01	2026-03-01 11:40:34.172613+00
2	2026-03-02	2026-03-01 14:21:06.244668+00
3	2026-03-04	2026-03-01 16:20:30.553695+00
4	2026-03-11	2026-03-01 16:20:32.113137+00
5	2026-03-12	2026-03-01 16:20:35.200903+00
6	2026-03-19	2026-03-01 16:20:35.845642+00
7	2026-03-17	2026-03-01 16:20:36.413395+00
8	2026-03-16	2026-03-01 16:20:37.80848+00
9	2026-02-17	2026-03-01 17:07:49.082683+00
10	2026-02-09	2026-03-01 17:09:21.102978+00
11	2026-02-10	2026-03-01 17:09:22.500782+00
12	2026-02-11	2026-03-01 17:09:23.853324+00
13	2026-02-12	2026-03-01 17:09:25.245202+00
14	2026-02-13	2026-03-01 17:09:26.547332+00
15	2026-02-16	2026-03-01 17:10:18.576891+00
16	2026-02-18	2026-03-01 17:10:21.908849+00
17	2026-02-19	2026-03-01 17:10:23.527494+00
18	2026-02-20	2026-03-01 17:10:24.96307+00
19	2026-02-23	2026-03-01 17:11:16.612501+00
20	2026-02-24	2026-03-01 17:11:18.162275+00
21	2026-02-25	2026-03-01 17:11:19.767181+00
22	2026-02-26	2026-03-01 17:11:21.282234+00
23	2026-02-27	2026-03-01 17:11:22.645321+00
\.


--
-- Data for Name: goal_tags; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.goal_tags (goal_id, tag_id) FROM stdin;
1	20
2	16
3	9
4	20
5	9
6	16
\.


--
-- Data for Name: goal_tasks; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.goal_tasks (goal_id, task_id) FROM stdin;
\.


--
-- Data for Name: goals; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.goals (id, title, description, target_date, status, completed_at, created_at) FROM stdin;
1	Ship treesync v0.4 stable release	Build out the full conflict resolution feature set (KeepLatest, ContentHash, Ask strategies), complete telemetry with privacy controls, pass integration tests on macOS, Linux, and Windows, and cut a stable release to crates.io.	2026-04-30	active	\N	2026-03-01 17:35:53.173099+00
2	Land a meaningful contribution to vex	Identify a real bug in the vex Rust linting framework, write a reproducer, implement and test a fix, get it merged by the maintainers, and document the experience. Follow up with vex#602 once the initial PR is merged.	2026-03-15	active	\N	2026-03-01 17:35:53.356679+00
3	Maintain a consistent daily movement practice through Q1	Hit both a morning yoga session and a gym session on every weekday. Alternating push/pull/leg days at the gym; yoga style varied daily (vinyasa, yin, restorative, strength flow). Dogs get a walk every day regardless.	2026-03-31	active	\N	2026-03-01 17:35:53.532328+00
4	Ship treesync v0.4 stable release	Build out the full conflict resolution feature set (KeepLatest, ContentHash, Ask strategies), complete telemetry with privacy controls, pass integration tests on macOS, Linux, and Windows, and cut a stable release to crates.io.	2026-04-30	active	\N	2026-03-01 17:35:57.289972+00
5	Maintain a consistent daily movement practice through Q1	Hit both a morning yoga session and a gym session on every weekday. Alternating push/pull/leg days at the gym; yoga style varied daily (vinyasa, yin, restorative, strength flow). Dogs get a walk every day regardless.	2026-03-31	active	\N	2026-03-01 17:36:04.247308+00
6	Land a meaningful contribution to vex	Identify a real bug in the vex Rust linting framework, write a reproducer, implement and test a fix, get it merged by the maintainers, and document the experience. Follow up with vex#602 once the initial PR lands.	2026-03-15	active	\N	2026-03-01 17:36:04.247771+00
\.


--
-- Data for Name: reminders; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.reminders (id, task_id, remind_at, message, is_delivered) FROM stdin;
\.


--
-- Data for Name: roadblocks; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.roadblocks (id, day_id, content, updated_at) FROM stdin;
3	22	treesync#234 (data loss concern on interrupted sync) required priority attention mid-afternoon. Turned out to be user error, but the error message was genuinely misleading — fixed the messaging and added a warning to the docs.	2026-03-01 17:17:49.423142+00
4	15	vex codebase is more complex than expected. Needed a full morning of reading before I could safely touch the lint infrastructure.	2026-03-01 17:17:49.424412+00
2	20	Windows CI kept timing out on file watcher integration tests — NTFS delivers events in a different order than inotify, required a platform-specific test re-ordering.	2026-03-01 17:18:51.565344+00
5	18	Lost an hour chasing a clippy warning that turned out to be a false positive in the new edition — had to add an allow attribute and file a bug upstream.	2026-03-01 17:18:51.567343+00
1	12	Race condition in async watcher tests — dropped events under rapid write load blocked progress for ~3 hours. Fixed, but needs a follow-up comment in the code explaining the invariant.	2026-03-01 17:17:49.423854+00
\.


--
-- Data for Name: settings; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.settings (key, value) FROM stdin;
recurring_days_off	["saturday", "sunday"]
timer_display	false
\.


--
-- Data for Name: tags; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.tags (id, name) FROM stdin;
1	rust
2	treesync
3	oss
4	architecture
5	testing
6	dogs
7	community
8	yoga
9	wellness
10	planning
11	devops
12	gym
13	fitness
14	learning
15	debugging
16	vex
17	home
18	performance
19	writing
20	treesync-v4
\.


--
-- Data for Name: task_tags; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.task_tags (task_id, tag_id) FROM stdin;
1	1
1	2
1	3
1	4
91	20
100	20
109	20
120	20
129	20
130	20
4	2
4	3
5	6
6	2
6	3
6	7
7	8
7	9
8	10
9	1
9	11
10	1
10	2
10	3
112	20
114	20
16	9
34	9
52	9
70	9
13	2
13	3
13	7
14	6
15	2
15	3
16	12
16	13
17	1
17	14
18	6
88	9
106	9
124	9
21	1
21	2
21	15
22	2
22	3
23	6
24	1
24	16
24	3
25	8
25	9
26	1
26	14
27	17
28	1
28	2
28	3
31	2
31	3
32	1
32	2
32	11
33	6
34	12
34	13
35	1
35	14
35	19
36	19
36	7
37	1
37	2
37	3
40	2
40	3
41	6
42	2
42	19
42	7
43	8
43	9
44	10
46	1
46	16
46	3
46	15
49	16
49	3
50	6
51	2
51	3
52	12
52	13
53	1
53	16
53	14
54	10
55	1
55	16
55	3
58	16
58	3
58	7
59	6
60	1
60	2
60	11
61	8
61	9
62	16
62	3
62	14
63	17
64	1
64	2
64	5
67	2
67	16
67	3
68	6
69	2
69	3
70	12
70	13
71	19
71	2
71	7
72	6
73	1
73	2
73	4
76	2
76	7
77	6
79	8
79	9
80	19
80	10
81	17
82	1
82	2
82	19
82	4
85	2
85	7
85	3
86	6
87	2
87	3
88	12
88	13
89	10
91	1
91	2
91	3
94	16
94	3
94	7
95	6
96	2
96	11
97	8
97	9
98	1
98	14
99	17
100	1
100	2
100	3
103	16
103	3
104	6
105	1
105	2
105	15
106	12
106	13
107	2
107	16
107	3
108	6
109	1
109	2
109	18
112	2
112	7
112	3
113	6
114	2
114	3
114	10
115	8
115	9
116	1
116	14
117	6
117	17
120	1
120	2
120	3
122	6
123	2
123	3
124	12
124	13
125	2
125	19
125	3
126	8
126	9
129	1
129	2
129	5
130	2
130	3
131	6
132	19
132	7
133	8
133	9
134	10
134	2
136	2
136	3
137	17
138	2
138	16
138	11
139	10
140	2
140	11
141	2
141	3
141	7
142	19
142	18
\.


--
-- Data for Name: task_templates; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.task_templates (id, title, description, category, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.tasks (id, day_id, category, title, description, status, order_index, completed_at) FROM stdin;
4	10	short_task	Triage open issues on treesync repo (12 new)	\N	completed	0	2026-03-01 17:11:57.904966+00
5	10	short_task	Morning walk with Mochi and Biscuit	\N	completed	1	2026-03-01 17:11:58.091674+00
6	10	short_task	Reply to contributor questions on Discord	\N	completed	2	2026-03-01 17:11:58.271622+00
7	10	maintenance	Morning yoga — sun salutation flow (40 min)	\N	completed	0	2026-03-01 17:11:58.453523+00
8	10	maintenance	Weekly planning session and goal review	\N	completed	1	2026-03-01 17:11:58.634861+00
9	10	maintenance	Update local dev dependencies across projects	\N	completed	2	2026-03-01 17:11:58.812076+00
13	11	short_task	Review and merge 2 community PRs on treesync	\N	completed	0	2026-03-01 17:11:59.540661+00
14	11	short_task	Lunch walk with Mochi and Biscuit — park route	\N	completed	1	2026-03-01 17:11:59.751696+00
15	11	short_task	Update treesync CHANGELOG and bump version	\N	completed	2	2026-03-01 17:11:59.973378+00
16	11	maintenance	Morning gym — push day (60 min)	\N	completed	0	2026-03-01 17:12:00.245837+00
17	11	maintenance	Read: Rust async book chapter on select!	\N	completed	1	2026-03-01 17:12:00.399896+00
21	12	deep_work	Debug event race condition in async watcher tests	\N	completed	2	2026-03-01 17:12:01.111882+00
22	12	short_task	Respond to treesync#201 — Windows path handling bug	\N	completed	0	2026-03-01 17:12:01.288588+00
23	12	short_task	Evening dog walk — river route with Mochi and Biscuit	\N	completed	1	2026-03-01 17:12:01.46853+00
24	12	short_task	Open issue on vex: false positive in lifetime lints	\N	completed	2	2026-03-01 17:12:01.643051+00
25	12	maintenance	Morning yoga — hip opener flow (45 min)	\N	completed	0	2026-03-01 17:12:01.820187+00
27	12	maintenance	Grocery order for the week	\N	completed	2	2026-03-01 17:12:02.248544+00
28	13	deep_work	Implement --dry-run flag with diff output for treesync	\N	completed	0	2026-03-01 17:12:02.430277+00
31	13	short_task	Open PR: treesync dry-run and progress features	\N	completed	0	2026-03-01 17:12:02.98498+00
32	13	short_task	Fix CI failure — update MSRV to Rust 1.82 in Cargo.toml	\N	completed	1	2026-03-01 17:12:03.160095+00
33	13	short_task	Drop off Biscuit at dog groomer	\N	completed	2	2026-03-01 17:12:03.429776+00
34	13	maintenance	Morning gym — pull day (60 min)	\N	completed	0	2026-03-01 17:12:03.570408+00
36	13	maintenance	Respond to comments on Rust blog post	\N	completed	2	2026-03-01 17:12:03.859521+00
37	14	deep_work	Code review and iterate on treesync PR feedback	\N	completed	0	2026-03-01 17:12:04.078878+00
40	14	short_task	Merge treesync PR after CI passes	\N	completed	0	2026-03-01 17:12:04.644543+00
41	14	short_task	Long Friday trail walk with Mochi and Biscuit	\N	completed	1	2026-03-01 17:12:04.786226+00
42	14	short_task	Post treesync v0.3-rc1 announcement on dev.to	\N	completed	2	2026-03-01 17:12:05.00063+00
43	14	maintenance	Morning yoga — restorative flow (30 min)	\N	completed	0	2026-03-01 17:12:05.146883+00
46	15	deep_work	Investigate and fix vex false positive: async lifetime lints	\N	completed	0	2026-03-01 17:12:05.656386+00
49	15	short_task	Open draft PR on vex with fix and test coverage	\N	completed	0	2026-03-01 17:12:06.266448+00
50	15	short_task	Morning dog walk — neighborhood loop	\N	completed	1	2026-03-01 17:12:06.412846+00
52	15	maintenance	Morning gym — leg day (60 min)	\N	completed	0	2026-03-01 17:12:29.635425+00
53	15	maintenance	Review vex codebase architecture before contributing	\N	completed	1	2026-03-01 17:12:29.843051+00
54	15	maintenance	Set weekly sprint goals and update project board	\N	completed	2	2026-03-01 17:12:30.05945+00
55	9	deep_work	Iterate on vex PR based on maintainer review feedback	\N	completed	0	2026-03-01 17:12:30.263473+00
58	9	short_task	Reply to vex maintainer review comments	\N	completed	0	2026-03-01 17:12:30.914449+00
59	9	short_task	Midday park walk with Mochi and Biscuit	\N	completed	1	2026-03-01 17:12:31.124424+00
61	9	maintenance	Morning yoga — strength flow (50 min)	\N	completed	0	2026-03-01 17:12:31.538283+00
62	9	maintenance	Read two vex backlog issues for future contribution ideas	\N	completed	1	2026-03-01 17:12:31.753125+00
63	9	maintenance	Order new standing desk mat	\N	completed	2	2026-03-01 17:12:31.964268+00
64	16	deep_work	Final pre-release testing of treesync v0.3 on macOS and Linux	\N	completed	0	2026-03-01 17:12:32.165939+00
67	16	short_task	Reply to 6 GitHub notifications across treesync and vex	\N	completed	0	2026-03-01 17:12:32.786923+00
68	16	short_task	Long sunny trail walk with Mochi and Biscuit (45 min)	\N	completed	1	2026-03-01 17:12:32.986044+00
69	16	short_task	Publish treesync v0.3 to crates.io	\N	completed	2	2026-03-01 17:12:33.183456+00
70	16	maintenance	Morning gym — push day (60 min)	\N	completed	0	2026-03-01 17:12:33.381859+00
72	16	maintenance	Mochi's annual vet checkup	\N	completed	2	2026-03-01 17:12:33.780019+00
73	17	deep_work	Begin treesync v0.4 planning: conflict resolution design	\N	completed	0	2026-03-01 17:12:33.983205+00
1	10	deep_work	Design treesync v0.3 async file watcher architecture	\N	completed	0	2026-03-01 17:11:57.226582+00
10	11	deep_work	Implement debouncing logic for FileWatcher events	\N	completed	0	2026-03-01 17:11:58.994023+00
18	11	maintenance	Schedule Mochi's vet checkup appointment	\N	completed	2	2026-03-01 17:12:00.57697+00
26	12	maintenance	Review Rust 2024 edition release notes	\N	completed	1	2026-03-01 17:12:02.082041+00
35	13	maintenance	Write dev notes on async patterns learned this week	\N	completed	1	2026-03-01 17:12:03.715852+00
44	14	maintenance	Weekly retro — what went well and blockers	\N	completed	1	2026-03-01 17:12:05.296967+00
51	15	short_task	Triage treesync issues opened over the weekend (8 new)	\N	completed	2	2026-03-01 17:12:29.460613+00
60	9	short_task	Test treesync on stable, beta, and nightly Rust channels	\N	completed	2	2026-03-01 17:12:31.324556+00
71	16	maintenance	Write dev blog post about treesync v0.3 release	\N	completed	1	2026-03-01 17:12:33.582073+00
76	17	short_task	Respond to treesync v0.3 user feedback on Reddit	\N	completed	0	2026-03-01 17:12:34.589315+00
77	17	short_task	Afternoon dog walk — Mochi and Biscuit loop	\N	completed	1	2026-03-01 17:12:34.797154+00
79	17	maintenance	Morning yoga — yin yoga (45 min)	\N	completed	0	2026-03-01 17:12:35.225866+00
80	17	maintenance	Write journal: v0.3 release retrospective notes	\N	completed	1	2026-03-01 17:12:35.42668+00
81	17	maintenance	Adjust monitor stand for better ergonomics	\N	completed	2	2026-03-01 17:12:35.629791+00
82	18	deep_work	Write treesync v0.4 design RFC document	\N	completed	0	2026-03-01 17:12:35.834398+00
85	18	short_task	Share v0.4 RFC on treesync Discussions for community input	\N	completed	0	2026-03-01 17:12:36.468797+00
86	18	short_task	Riverside path walk with Mochi and Biscuit	\N	completed	1	2026-03-01 17:12:36.630835+00
87	18	short_task	Merge approved community PR into treesync main	\N	completed	2	2026-03-01 17:12:36.789283+00
88	18	maintenance	Morning gym — pull day (60 min)	\N	completed	0	2026-03-01 17:12:36.949418+00
91	19	deep_work	Implement KeepLatest conflict resolution strategy	\N	completed	0	2026-03-01 17:12:37.446269+00
94	19	short_task	Review 4 new PRs on vex and leave feedback	\N	completed	0	2026-03-01 17:12:38.127082+00
95	19	short_task	Morning neighborhood walk with Mochi and Biscuit	\N	completed	1	2026-03-01 17:12:38.376932+00
96	19	short_task	Update GitHub Actions to cache Cargo registry	\N	completed	2	2026-03-01 17:12:38.618094+00
98	19	maintenance	Catch up on This Week in Rust newsletter	\N	completed	1	2026-03-01 17:12:38.943564+00
99	19	maintenance	Meal prep healthy lunches for the week	\N	completed	2	2026-03-01 17:12:39.192666+00
100	20	deep_work	Implement MergeConflict enum and structured error reporting	\N	completed	0	2026-03-01 17:12:39.353134+00
103	20	short_task	Post update on vex PR — addressed all review notes	\N	completed	0	2026-03-01 17:13:00.445921+00
104	20	short_task	Cold morning walk with Mochi and Biscuit	\N	completed	1	2026-03-01 17:13:00.661169+00
106	20	maintenance	Morning gym — leg day (60 min)	\N	completed	0	2026-03-01 17:13:01.098536+00
107	20	maintenance	Archive GitHub notification backlog	\N	completed	1	2026-03-01 17:13:01.336802+00
108	20	maintenance	Biscuit's annual vet checkup and shots	\N	completed	2	2026-03-01 17:13:01.552508+00
109	21	deep_work	Performance optimization: reduce memory allocations in hot sync path	\N	completed	0	2026-03-01 17:13:01.783336+00
112	21	short_task	Reply to treesync v0.4 RFC community feedback	\N	completed	0	2026-03-01 17:13:02.460646+00
114	21	short_task	Update treesync public roadmap based on RFC responses	\N	completed	2	2026-03-01 17:13:02.906582+00
115	21	maintenance	Morning yoga — slow rainy-day flow (40 min)	\N	completed	0	2026-03-01 17:13:03.125464+00
116	21	maintenance	Read: zero-cost async patterns in Rust	\N	completed	1	2026-03-01 17:13:03.34842+00
117	21	maintenance	Monthly restock: order dog food and treats	\N	completed	2	2026-03-01 17:13:03.573289+00
120	22	deep_work	Add telemetry opt-in for sync performance metrics	\N	in_progress	2	\N
122	22	short_task	Post-rain trail walk with Mochi and Biscuit	\N	completed	1	2026-03-01 17:13:04.530263+00
124	22	maintenance	Morning gym — push day (60 min)	\N	completed	0	2026-03-01 17:13:04.910425+00
125	22	maintenance	Update treesync CONTRIBUTING.md and contributor guide	\N	completed	1	2026-03-01 17:13:05.090144+00
126	22	maintenance	Evening yoga — unwind session (30 min)	\N	completed	2	2026-03-01 17:13:05.269766+00
129	23	deep_work	Final integration testing for treesync v0.4-alpha release	\N	in_progress	2	\N
130	23	short_task	Tag and publish treesync v0.4-alpha to crates.io	\N	completed	0	2026-03-01 17:13:05.973873+00
131	23	short_task	Long sunny Friday trail walk — Mochi and Biscuit	\N	completed	1	2026-03-01 17:13:06.145864+00
132	23	short_task	Write week summary post on dev.to	\N	completed	2	2026-03-01 17:13:06.331361+00
133	23	maintenance	Morning yoga — energizing flow (45 min)	\N	completed	0	2026-03-01 17:13:06.508853+00
89	18	maintenance	Weekly retro and sprint planning for next week	\N	completed	1	2026-03-01 17:12:37.121644+00
97	19	maintenance	Morning yoga — vinyasa flow (45 min)	\N	completed	0	2026-03-01 17:12:38.77577+00
105	20	short_task	Fix flaky test: treesync::tests::test_event_ordering	\N	completed	2	2026-03-01 17:13:00.882543+00
113	21	short_task	Indoor rainy day play session with Mochi and Biscuit	\N	completed	1	2026-03-01 17:13:02.684986+00
123	22	short_task	Respond to treesync#234 — high-priority data loss concern	\N	completed	2	2026-03-01 17:13:04.726778+00
134	23	maintenance	Weekly retro: v0.4-alpha shipped!	\N	completed	1	2026-03-01 17:13:06.682258+00
136	11	short_task	Check treesync download stats and stars on crates.io	\N	pending	3	\N
137	12	maintenance	Tidy home office and restock desk supplies	\N	pending	3	\N
138	9	short_task	Run cargo audit on treesync and vex dependencies	\N	pending	3	\N
139	17	maintenance	Prep next week's task list and Monday morning plan	\N	pending	3	\N
140	20	short_task	Check Windows GitHub Actions runner configuration	\N	pending	3	\N
141	20	short_task	Post Windows CI debugging progress in treesync issue	\N	pending	4	\N
142	21	maintenance	Add performance benchmark notes to dev journal	\N	pending	3	\N
143	\N	deep_work	Add ~/.treesync.toml config file support	Allow users to persist --conflict-strategy, exclude patterns, and remote targets in a config file rather than passing flags every run. Follow-up to the v0.4 CLI flag work.	pending	0	\N
144	\N	deep_work	Write blog post: contributing to vex as a first-time contributor	Document the experience of finding, reproducing, fixing, and landing vex#589. Useful for other Rust devs who want to contribute to compiler tooling but find it intimidating.	pending	0	\N
145	\N	deep_work	Implement Ask conflict strategy — prompt user on conflict	Third conflict resolution strategy for treesync v0.4 alongside KeepLatest and ContentHash. Opens an interactive prompt when a conflict is detected so the user can decide per-file.	pending	0	\N
146	\N	deep_work	Write treesync getting-started tutorial for docs site	Step-by-step guide covering install, first sync, remote targets, and conflict resolution. Builds on the CLI examples doc written for the v0.3 release.	pending	0	\N
147	\N	deep_work	Add .treesyncignore file support (gitignore-style patterns)	Users have been asking for glob-based exclusion patterns since v0.3. Follow-up to the recursive directory scanning work from Feb 10.	pending	0	\N
148	\N	deep_work	Profile treesync on large monorepos (10k+ files)	The criterion benchmarks from Feb 25 were run on small test trees. Need to validate perf on realistic large repos — the 4ms sync loop result may not hold at scale.	pending	0	\N
149	\N	deep_work	Investigate vex#602 — nested async closure false positive	A new false positive was opened after the #589 fix was merged. Nested async closures with captured borrows still trigger the lint incorrectly. Natural continuation of the vex contribution from week 2.	pending	0	\N
150	\N	short_task	Plan longer weekend trail route for Mochi and Biscuit	The Friday trail walks have been great but it would be good to find a longer half-day route for weekends. Research dog-friendly trails within 30 min drive.	pending	0	\N
151	\N	deep_work	Resolve treesync#201 — Windows extended path (\\\\?\\) support	The Windows path handling bug responded to on Feb 11 is still open. The root cause is paths longer than MAX_PATH that require the \\\\?\\ prefix. Needs a proper fix, not just documentation.	pending	0	\N
152	\N	deep_work	Write blog post: async Rust patterns I learned building treesync	Consolidates the dev notes written on Feb 12 into a proper article: debouncing, race condition debugging, tokio-stream event pipelines. Good SEO for the treesync project.	pending	0	\N
153	\N	short_task	Submit treesync talk proposal to RustConf 2026	The async file sync architecture and conflict resolution design would make a solid 25-min talk. Deadline typically in spring. Build on the RFC and design doc written in Feb.	pending	0	\N
154	\N	short_task	Set up criterion benchmark tracking dashboard (Bencher.dev)	Now that benchmarks are in CI (Feb 26), wire them up to Bencher.dev for historical tracking and regression alerts. Prevents perf regressions from sneaking in unnoticed.	pending	0	\N
155	\N	short_task	Research ergonomic standing desk upgrade	The monitor stand adjustment on Feb 19 was a band-aid. Worth properly evaluating a height-adjustable desk. Budget ~$600. Research options and reviews.	pending	0	\N
\.


--
-- Data for Name: template_schedules; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.template_schedules (id, template_id, recurrence, anchor_date, next_run_date, created_at) FROM stdin;
\.


--
-- Data for Name: template_tags; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.template_tags (template_id, tag_id) FROM stdin;
\.


--
-- Data for Name: timer_sessions; Type: TABLE DATA; Schema: public; Owner: oliver
--

COPY public.timer_sessions (id, task_id, started_at, ended_at, duration_seconds) FROM stdin;
\.


--
-- Name: daily_notes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oliver
--

SELECT pg_catalog.setval('public.daily_notes_id_seq', 12, true);


--
-- Name: day_metadata_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oliver
--

SELECT pg_catalog.setval('public.day_metadata_id_seq', 15, true);


--
-- Name: day_offs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oliver
--

SELECT pg_catalog.setval('public.day_offs_id_seq', 2, true);


--
-- Name: day_ratings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oliver
--

SELECT pg_catalog.setval('public.day_ratings_id_seq', 15, true);


--
-- Name: days_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oliver
--

SELECT pg_catalog.setval('public.days_id_seq', 23, true);


--
-- Name: goals_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oliver
--

SELECT pg_catalog.setval('public.goals_id_seq', 6, true);


--
-- Name: reminders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oliver
--

SELECT pg_catalog.setval('public.reminders_id_seq', 1, false);


--
-- Name: roadblocks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oliver
--

SELECT pg_catalog.setval('public.roadblocks_id_seq', 5, true);


--
-- Name: tags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oliver
--

SELECT pg_catalog.setval('public.tags_id_seq', 20, true);


--
-- Name: task_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oliver
--

SELECT pg_catalog.setval('public.task_templates_id_seq', 1, false);


--
-- Name: tasks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oliver
--

SELECT pg_catalog.setval('public.tasks_id_seq', 155, true);


--
-- Name: template_schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oliver
--

SELECT pg_catalog.setval('public.template_schedules_id_seq', 1, false);


--
-- Name: timer_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oliver
--

SELECT pg_catalog.setval('public.timer_sessions_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: daily_notes daily_notes_day_id_key; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.daily_notes
    ADD CONSTRAINT daily_notes_day_id_key UNIQUE (day_id);


--
-- Name: daily_notes daily_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.daily_notes
    ADD CONSTRAINT daily_notes_pkey PRIMARY KEY (id);


--
-- Name: day_metadata day_metadata_day_id_key; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.day_metadata
    ADD CONSTRAINT day_metadata_day_id_key UNIQUE (day_id);


--
-- Name: day_metadata day_metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.day_metadata
    ADD CONSTRAINT day_metadata_pkey PRIMARY KEY (id);


--
-- Name: day_offs day_offs_day_id_key; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.day_offs
    ADD CONSTRAINT day_offs_day_id_key UNIQUE (day_id);


--
-- Name: day_offs day_offs_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.day_offs
    ADD CONSTRAINT day_offs_pkey PRIMARY KEY (id);


--
-- Name: day_ratings day_ratings_day_id_key; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.day_ratings
    ADD CONSTRAINT day_ratings_day_id_key UNIQUE (day_id);


--
-- Name: day_ratings day_ratings_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.day_ratings
    ADD CONSTRAINT day_ratings_pkey PRIMARY KEY (id);


--
-- Name: days days_date_key; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.days
    ADD CONSTRAINT days_date_key UNIQUE (date);


--
-- Name: days days_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.days
    ADD CONSTRAINT days_pkey PRIMARY KEY (id);


--
-- Name: goal_tags goal_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.goal_tags
    ADD CONSTRAINT goal_tags_pkey PRIMARY KEY (goal_id, tag_id);


--
-- Name: goal_tasks goal_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.goal_tasks
    ADD CONSTRAINT goal_tasks_pkey PRIMARY KEY (goal_id, task_id);


--
-- Name: goals goals_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.goals
    ADD CONSTRAINT goals_pkey PRIMARY KEY (id);


--
-- Name: reminders reminders_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.reminders
    ADD CONSTRAINT reminders_pkey PRIMARY KEY (id);


--
-- Name: roadblocks roadblocks_day_id_key; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.roadblocks
    ADD CONSTRAINT roadblocks_day_id_key UNIQUE (day_id);


--
-- Name: roadblocks roadblocks_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.roadblocks
    ADD CONSTRAINT roadblocks_pkey PRIMARY KEY (id);


--
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (key);


--
-- Name: tags tags_name_key; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_name_key UNIQUE (name);


--
-- Name: tags tags_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (id);


--
-- Name: task_tags task_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.task_tags
    ADD CONSTRAINT task_tags_pkey PRIMARY KEY (task_id, tag_id);


--
-- Name: task_templates task_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.task_templates
    ADD CONSTRAINT task_templates_pkey PRIMARY KEY (id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: template_schedules template_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.template_schedules
    ADD CONSTRAINT template_schedules_pkey PRIMARY KEY (id);


--
-- Name: template_tags template_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.template_tags
    ADD CONSTRAINT template_tags_pkey PRIMARY KEY (template_id, tag_id);


--
-- Name: timer_sessions timer_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.timer_sessions
    ADD CONSTRAINT timer_sessions_pkey PRIMARY KEY (id);


--
-- Name: ix_daily_notes_day_id; Type: INDEX; Schema: public; Owner: oliver
--

CREATE UNIQUE INDEX ix_daily_notes_day_id ON public.daily_notes USING btree (day_id);


--
-- Name: ix_day_ratings_day_id; Type: INDEX; Schema: public; Owner: oliver
--

CREATE UNIQUE INDEX ix_day_ratings_day_id ON public.day_ratings USING btree (day_id);


--
-- Name: ix_days_date; Type: INDEX; Schema: public; Owner: oliver
--

CREATE INDEX ix_days_date ON public.days USING btree (date);


--
-- Name: ix_reminders_task_id; Type: INDEX; Schema: public; Owner: oliver
--

CREATE INDEX ix_reminders_task_id ON public.reminders USING btree (task_id);


--
-- Name: ix_roadblocks_day_id; Type: INDEX; Schema: public; Owner: oliver
--

CREATE UNIQUE INDEX ix_roadblocks_day_id ON public.roadblocks USING btree (day_id);


--
-- Name: ix_tags_name; Type: INDEX; Schema: public; Owner: oliver
--

CREATE INDEX ix_tags_name ON public.tags USING btree (name);


--
-- Name: ix_tasks_day_id; Type: INDEX; Schema: public; Owner: oliver
--

CREATE INDEX ix_tasks_day_id ON public.tasks USING btree (day_id);


--
-- Name: ix_template_schedules_next_run_date; Type: INDEX; Schema: public; Owner: oliver
--

CREATE INDEX ix_template_schedules_next_run_date ON public.template_schedules USING btree (next_run_date);


--
-- Name: ix_timer_sessions_task_id; Type: INDEX; Schema: public; Owner: oliver
--

CREATE INDEX ix_timer_sessions_task_id ON public.timer_sessions USING btree (task_id);


--
-- Name: daily_notes daily_notes_day_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.daily_notes
    ADD CONSTRAINT daily_notes_day_id_fkey FOREIGN KEY (day_id) REFERENCES public.days(id) ON DELETE CASCADE;


--
-- Name: day_metadata day_metadata_day_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.day_metadata
    ADD CONSTRAINT day_metadata_day_id_fkey FOREIGN KEY (day_id) REFERENCES public.days(id) ON DELETE CASCADE;


--
-- Name: day_offs day_offs_day_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.day_offs
    ADD CONSTRAINT day_offs_day_id_fkey FOREIGN KEY (day_id) REFERENCES public.days(id) ON DELETE CASCADE;


--
-- Name: day_ratings day_ratings_day_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.day_ratings
    ADD CONSTRAINT day_ratings_day_id_fkey FOREIGN KEY (day_id) REFERENCES public.days(id) ON DELETE CASCADE;


--
-- Name: goal_tags goal_tags_goal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.goal_tags
    ADD CONSTRAINT goal_tags_goal_id_fkey FOREIGN KEY (goal_id) REFERENCES public.goals(id) ON DELETE CASCADE;


--
-- Name: goal_tags goal_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.goal_tags
    ADD CONSTRAINT goal_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: goal_tasks goal_tasks_goal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.goal_tasks
    ADD CONSTRAINT goal_tasks_goal_id_fkey FOREIGN KEY (goal_id) REFERENCES public.goals(id) ON DELETE CASCADE;


--
-- Name: goal_tasks goal_tasks_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.goal_tasks
    ADD CONSTRAINT goal_tasks_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: reminders reminders_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.reminders
    ADD CONSTRAINT reminders_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: roadblocks roadblocks_day_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.roadblocks
    ADD CONSTRAINT roadblocks_day_id_fkey FOREIGN KEY (day_id) REFERENCES public.days(id) ON DELETE CASCADE;


--
-- Name: task_tags task_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.task_tags
    ADD CONSTRAINT task_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: task_tags task_tags_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.task_tags
    ADD CONSTRAINT task_tags_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: tasks tasks_day_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_day_id_fkey FOREIGN KEY (day_id) REFERENCES public.days(id) ON DELETE CASCADE;


--
-- Name: template_schedules template_schedules_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.template_schedules
    ADD CONSTRAINT template_schedules_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.task_templates(id) ON DELETE CASCADE;


--
-- Name: template_tags template_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.template_tags
    ADD CONSTRAINT template_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: template_tags template_tags_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.template_tags
    ADD CONSTRAINT template_tags_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.task_templates(id) ON DELETE CASCADE;


--
-- Name: timer_sessions timer_sessions_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: oliver
--

ALTER TABLE ONLY public.timer_sessions
    ADD CONSTRAINT timer_sessions_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 3Hhl5eXrSZAK6x0qzWVFGhbXy0e2GGYvG95AUyKgAKut6g19etqyDC4yZTmuJAz

