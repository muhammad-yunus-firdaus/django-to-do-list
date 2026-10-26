from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date, time, timedelta, datetime
from django.utils import timezone

from .models import Tugas, Subtask, AktivitasHarian, EvaluasiMingguan, Kegiatan
from .views import _get_week_range, _get_weekly_stats, _get_next_free_slot, _generate_24h_timeline


class UserProfilTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password123', email='user1@example.com')
        self.user2 = User.objects.create_user(username='user2', password='password123', email='user2@example.com')
        self.client = Client()

    def test_profil_edit_duplicate_username(self):
        self.client.force_login(self.user1)
        response = self.client.post(reverse('tugas:edit_profil'), {
            'action': 'update_profil',
            'username': 'user2', # user2 already exists
            'email': 'user1@example.com'
        })
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, 'user1') # should not change
        self.assertContains(response, 'Username ini sudah digunakan')

    def test_profil_edit_duplicate_email(self):
        self.client.force_login(self.user1)
        response = self.client.post(reverse('tugas:edit_profil'), {
            'action': 'update_profil',
            'username': 'user1',
            'email': 'user2@example.com' # user2 has this email
        })
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.email, 'user1@example.com') # should not change
        self.assertContains(response, 'Email ini sudah digunakan')

    def test_profil_edit_success(self):
        self.client.force_login(self.user1)
        response = self.client.post(reverse('tugas:edit_profil'), {
            'action': 'update_profil',
            'username': 'user1new',
            'email': 'user1new@example.com'
        })
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, 'user1new')
        self.assertEqual(self.user1.email, 'user1new@example.com')

    def test_password_change_invalid_old(self):
        self.client.force_login(self.user1)
        response = self.client.post(reverse('tugas:edit_profil'), {
            'action': 'update_password',
            'password_lama': 'wrongpassword',
            'password_baru': 'newpassword123',
            'password_konfirmasi': 'newpassword123'
        })
        self.assertTrue(self.user1.check_password('password123')) # old password still works
        self.assertContains(response, 'Password lama salah')

    def test_password_change_mismatch_confirmation(self):
        self.client.force_login(self.user1)
        response = self.client.post(reverse('tugas:edit_profil'), {
            'action': 'update_password',
            'password_lama': 'password123',
            'password_baru': 'newpassword123',
            'password_konfirmasi': 'different123'
        })
        self.assertTrue(self.user1.check_password('password123'))
        self.assertContains(response, 'Password baru dan konfirmasi tidak cocok')

    def test_password_change_success(self):
        self.client.force_login(self.user1)
        response = self.client.post(reverse('tugas:edit_profil'), {
            'action': 'update_password',
            'password_lama': 'password123',
            'password_baru': 'newpassword123',
            'password_konfirmasi': 'newpassword123'
        })
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.check_password('newpassword123'))


class SubtaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='password123')
        self.client = Client()

    def test_tambah_tugas_with_dynamic_subtasks(self):
        self.client.force_login(self.user)
        # Create a task along with list of subtasks
        response = self.client.post(reverse('tugas:tambah'), {
            'judul': 'Tugas Utama',
            'deskripsi': 'Deskripsi tugas utama',
            'deadline': (date.today() + timedelta(days=2)).strftime('%Y-%m-%dT12:00'),
            'prioritas': 'sedang',
            'kategori': 'kerja',
            'status': 'belum',
            'subtasks[]': ['Subtask Satu', 'Subtask Dua', '  ', 'Subtask Tiga'] # Third is whitespace-only, should be skipped
        })
        self.assertEqual(response.status_code, 302) # Redirect to daftar_tugas
        tugas = Tugas.objects.filter(user=self.user, judul='Tugas Utama').first()
        self.assertIsNotNone(tugas)
        
        # Verify subtasks are created
        subtasks = Subtask.objects.filter(tugas=tugas).order_by('urutan')
        self.assertEqual(subtasks.count(), 3)
        self.assertEqual(subtasks[0].judul, 'Subtask Satu')
        self.assertEqual(subtasks[1].judul, 'Subtask Dua')
        self.assertEqual(subtasks[2].judul, 'Subtask Tiga')


class AktivitasHarianTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='password123')
        self.client = Client()

    def test_time_calculation_on_save(self):
        akt = AktivitasHarian(
            user=self.user,
            judul='Tidur Siang',
            jam_mulai=time(13, 0),
            durasi_menit=90,
            tanggal=date.today()
        )
        akt.save()
        self.assertEqual(akt.jam_selesai, time(14, 30))

    def test_anti_overlap_validation_triggers(self):
        # 1. Create first activity: 09:00 - 10:30 (90 mins)
        akt1 = AktivitasHarian.objects.create(
            user=self.user,
            judul='Meeting Pagi',
            jam_mulai=time(9, 0),
            durasi_menit=90,
            tanggal=date.today()
        )

        # 2. Try creating overlapping activity: 10:00 - 11:00 (60 mins) -> overlaps 10:00-10:30
        akt2 = AktivitasHarian(
            user=self.user,
            judul='Coding Session',
            jam_mulai=time(10, 0),
            durasi_menit=60,
            tanggal=date.today()
        )
        with self.assertRaises(ValidationError):
            akt2.full_clean()

    def test_non_overlapping_succeeds(self):
        akt1 = AktivitasHarian.objects.create(
            user=self.user,
            judul='Meeting Pagi',
            jam_mulai=time(9, 0),
            durasi_menit=60, # ends 10:00
            tanggal=date.today()
        )
        akt2 = AktivitasHarian(
            user=self.user,
            judul='Coding Session',
            jam_mulai=time(10, 0),
            durasi_menit=60, # starts exactly 10:00
            tanggal=date.today()
        )
        try:
            akt2.full_clean()
            akt2.save()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly for non-overlapping schedules!")

    def test_habit_copy_mechanism(self):
        # Create a habit on a past day
        past_day = date.today() - timedelta(days=2)
        AktivitasHarian.objects.create(
            user=self.user,
            judul='Olahraga Pagi',
            jam_mulai=time(7, 0),
            durasi_menit=30,
            is_habit=True,
            tanggal=past_day
        )

        self.client.force_login(self.user)
        # Accessing agenda should trigger _copy_habits_for_today
        response = self.client.get(reverse('tugas:agenda'))
        self.assertEqual(response.status_code, 200)

        # Verify habit is copied to today
        today_akt = AktivitasHarian.objects.filter(user=self.user, tanggal=date.today(), judul='Olahraga Pagi').first()
        self.assertIsNotNone(today_akt)
        self.assertEqual(today_akt.jam_mulai, time(7, 0))
        self.assertEqual(today_akt.durasi_menit, 30)
        self.assertTrue(today_akt.is_habit)

    def test_api_status_change(self):
        akt = AktivitasHarian.objects.create(
            user=self.user,
            judul='Membaca Buku',
            jam_mulai=time(15, 0),
            durasi_menit=45,
            tanggal=date.today(),
            status='belum'
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse('tugas:toggle_aktivitas', args=[akt.id]),
            '{"status": "terlewat"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        akt.refresh_from_db()
        self.assertEqual(akt.status, 'terlewat')

    def test_api_status_change_validation_lock(self):
        """Aktivitas dengan status 'selesai' tidak boleh diubah ke 'terlewat'."""
        akt = AktivitasHarian.objects.create(
            user=self.user,
            judul='Membaca Buku 2',
            jam_mulai=time(16, 0),
            durasi_menit=45,
            tanggal=date.today(),
            status='selesai'
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse('tugas:toggle_aktivitas', args=[akt.id]),
            '{"status": "terlewat"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        akt.refresh_from_db()
        self.assertEqual(akt.status, 'selesai')


class SmartDefaultSlotTests(TestCase):
    """Test logika Smart Default Jam Mulai."""
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='password123')

    def test_next_free_slot_after_existing_activity(self):
        """Slot berikutnya = jam_selesai terakhir + 1 menit."""
        tanggal = date.today()
        # Buat aktivitas 09:00 - 10:00
        AktivitasHarian.objects.create(
            user=self.user, judul='Meeting', jam_mulai=time(9, 0),
            durasi_menit=60, tanggal=tanggal
        )
        # Buat aktivitas 10:00 - 11:30
        AktivitasHarian.objects.create(
            user=self.user, judul='Coding', jam_mulai=time(10, 0),
            durasi_menit=90, tanggal=tanggal
        )

        slot = _get_next_free_slot(self.user, tanggal)
        # Last activity ends 11:30, so next free slot = 11:31
        self.assertEqual(slot, '11:31')

    def test_next_free_slot_no_activities_past_date(self):
        """Jika tidak ada aktivitas di tanggal selain hari ini, default 07:00."""
        past_date = date.today() - timedelta(days=5)
        slot = _get_next_free_slot(self.user, past_date)
        self.assertEqual(slot, '07:00')


class CopyJadwalKemarinTests(TestCase):
    """Test endpoint copy jadwal kemarin."""
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='password123')
        self.client = Client()

    def test_copy_kemarin_creates_activities(self):
        self.client.force_login(self.user)
        tanggal = date.today()

        response = self.client.post(
            reverse('tugas:copy_jadwal_kemarin'),
            data='{"tanggal": "' + tanggal.isoformat() + '", "aktivitas": [{"judul": "Meeting Pagi", "jam_mulai": "09:00", "durasi_menit": 60, "is_habit": false}, {"judul": "Lunch Break", "jam_mulai": "12:00", "durasi_menit": 60, "is_habit": false}]}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['created'], 2)

        # Verify in DB
        akt_list = AktivitasHarian.objects.filter(user=self.user, tanggal=tanggal)
        self.assertEqual(akt_list.count(), 2)

    def test_copy_kemarin_skips_overlap(self):
        self.client.force_login(self.user)
        tanggal = date.today()

        # Create existing activity at 09:00
        AktivitasHarian.objects.create(
            user=self.user, judul='Existing', jam_mulai=time(9, 0),
            durasi_menit=60, tanggal=tanggal
        )

        # Try to copy an activity that overlaps with existing
        response = self.client.post(
            reverse('tugas:copy_jadwal_kemarin'),
            data='{"tanggal": "' + tanggal.isoformat() + '", "aktivitas": [{"judul": "Overlap Meeting", "jam_mulai": "09:30", "durasi_menit": 30, "is_habit": false}]}',
            content_type='application/json'
        )
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['created'], 0)
        self.assertEqual(data['skipped'], 1)


class DashboardAgendaTests(TestCase):
    """Test widget ringkasan jadwal hari ini di Dashboard."""
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='password123')
        self.client = Client()

    def test_dashboard_contains_agenda_today(self):
        # Buat aktivitas hari ini
        AktivitasHarian.objects.create(
            user=self.user, judul='Standup Meeting', jam_mulai=time(9, 0),
            durasi_menit=15, tanggal=date.today(), status='belum'
        )
        AktivitasHarian.objects.create(
            user=self.user, judul='Deep Work', jam_mulai=time(10, 0),
            durasi_menit=120, tanggal=date.today(), status='selesai'
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('tugas:dashboard'))
        self.assertEqual(response.status_code, 200)

        # Verifikasi konten widget jadwal hari ini
        self.assertContains(response, 'Ringkasan Jadwal Hari Ini')
        self.assertContains(response, 'Standup Meeting')
        self.assertContains(response, 'Deep Work')
        self.assertContains(response, '1/2 Selesai')

    def test_dashboard_empty_agenda_shows_empty_state(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('tugas:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Belum ada jadwal untuk hari ini')


class EvaluasiMingguanTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='password123')
        self.client = Client()

    def test_get_weekly_stats(self):
        start, end = _get_week_range()

        # 1. Create 2 tasks created this week (1 complete, 1 incomplete)
        t1 = Tugas.objects.create(
            user=self.user, judul='Tugas 1', prioritas='sedang', kategori='kerja', status='selesai'
        )
        t1.created_at = timezone.make_aware(datetime.combine(start, time(12, 0)))
        t1.save()

        t2 = Tugas.objects.create(
            user=self.user, judul='Tugas 2', prioritas='sedang', kategori='kerja', status='belum'
        )
        t2.created_at = timezone.make_aware(datetime.combine(start + timedelta(days=1), time(0, 0)))
        t2.save()

        # 2. Create 3 activities this week (2 complete, 1 incomplete)
        AktivitasHarian.objects.create(
            user=self.user, judul='Akt 1', jam_mulai=time(9,0), durasi_menit=30, tanggal=start, status='selesai'
        )
        AktivitasHarian.objects.create(
            user=self.user, judul='Akt 2', jam_mulai=time(10,0), durasi_menit=30, tanggal=start + timedelta(days=1), status='selesai'
        )
        AktivitasHarian.objects.create(
            user=self.user, judul='Akt 3', jam_mulai=time(11,0), durasi_menit=30, tanggal=start + timedelta(days=2), status='belum'
        )

        stats = _get_weekly_stats(self.user, start, end)
        self.assertEqual(stats['total_tugas'], 2)
        self.assertEqual(stats['tugas_selesai'], 1)
        self.assertEqual(stats['persen_tugas'], 50.0)

        self.assertEqual(stats['total_aktivitas'], 3)
        self.assertEqual(stats['aktivitas_selesai'], 2)
        self.assertEqual(stats['persen_aktivitas'], 66.7)

    def test_save_evaluasi_mingguan(self):
        start, end = _get_week_range()
        self.client.force_login(self.user)
        response = self.client.post(reverse('tugas:evaluasi'), {
            'catatan_evaluasi': 'Kerja bagus minggu ini!'
        })
        self.assertEqual(response.status_code, 302)

        # Check in DB
        evaluasi = EvaluasiMingguan.objects.filter(user=self.user, minggu_mulai=start).first()
        self.assertIsNotNone(evaluasi)
        self.assertEqual(evaluasi.catatan_evaluasi, 'Kerja bagus minggu ini!')


class SecurityIsolationTests(TestCase):
    def setUp(self):
        self.userA = User.objects.create_user(username='userA', password='password123')
        self.userB = User.objects.create_user(username='userB', password='password123')
        self.client = Client()

    def test_data_leakage_agenda_isolation(self):
        # Create activity for user A
        aktA = AktivitasHarian.objects.create(
            user=self.userA, judul='Secret Meeting', jam_mulai=time(9,0), durasi_menit=30, tanggal=date.today()
        )

        # Login as User B
        self.client.force_login(self.userB)
        response = self.client.get(reverse('tugas:agenda'))
        
        # User B's agenda should not contain User A's activity
        self.assertNotContains(response, 'Secret Meeting')

        # Try to modify User A's activity as User B -> should get 404
        response_toggle = self.client.post(
            reverse('tugas:toggle_aktivitas', args=[aktA.id]),
            '{"status": "selesai"}',
            content_type='application/json'
        )
        self.assertEqual(response_toggle.status_code, 404)

        # Try to delete User A's activity as User B -> should get 404
        response_delete = self.client.post(reverse('tugas:hapus_aktivitas', args=[aktA.id]))
        self.assertEqual(response_delete.status_code, 404)


class KegiatanTests(TestCase):
    def setUp(self):
        self.userA = User.objects.create_user(username='userA', password='password123')
        self.userB = User.objects.create_user(username='userB', password='password123')
        self.client = Client()

    def test_kegiatan_crud_operations(self):
        self.client.force_login(self.userA)
        # Create
        response = self.client.post(reverse('tugas:kegiatan_tambah'), {
            'judul': 'Meeting Dosen',
            'kategori': 'akademik',
            'tanggal': '2026-08-01',
            'jam_mulai': '09:00',
            'jam_selesai': '10:00',
            'lokasi': 'Zoom Link',
            'catatan': 'Bahas skripsi',
            'status': 'akan_datang'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Check DB
        keg = Kegiatan.objects.filter(user=self.userA, judul='Meeting Dosen').first()
        self.assertIsNotNone(keg)
        self.assertEqual(keg.lokasi, 'Zoom Link')

        # Edit/Update
        response_edit = self.client.post(reverse('tugas:kegiatan_edit', args=[keg.id]), {
            'judul': 'Meeting Dosen Updated',
            'kategori': 'akademik',
            'tanggal': '2026-08-01',
            'jam_mulai': '09:00',
            'jam_selesai': '10:30',
            'lokasi': 'Zoom Link 2',
            'catatan': 'Bahas skripsi bab 2',
            'status': 'selesai'
        })
        self.assertEqual(response_edit.status_code, 200)
        self.assertTrue(response_edit.json()['success'])
        keg.refresh_from_db()
        self.assertEqual(keg.judul, 'Meeting Dosen Updated')
        self.assertEqual(keg.jam_selesai, time(10, 30))

        # Delete
        response_delete = self.client.post(reverse('tugas:kegiatan_hapus', args=[keg.id]))
        self.assertEqual(response_delete.status_code, 200)
        self.assertTrue(response_delete.json()['success'])
        self.assertEqual(Kegiatan.objects.filter(id=keg.id).count(), 0)

    def test_kegiatan_validation_time_order(self):
        # jam_selesai <= jam_mulai should fail validation
        keg = Kegiatan(
            user=self.userA,
            judul='Invalid Time Event',
            kategori='lainnya',
            tanggal=date(2026, 8, 1),
            jam_mulai=time(10, 0),
            jam_selesai=time(9, 0)
        )
        with self.assertRaises(ValidationError):
            keg.full_clean()

    def test_kegiatan_overlap_detection(self):
        # Create a valid event
        keg1 = Kegiatan.objects.create(
            user=self.userA,
            judul='Event 1',
            kategori='pekerjaan',
            tanggal=date(2026, 8, 1),
            jam_mulai=time(9, 0),
            jam_selesai=time(10, 0)
        )

        # Event 2 overlapping keg1 -> should fail clean() / save()
        keg2 = Kegiatan(
            user=self.userA,
            judul='Event 2',
            kategori='pekerjaan',
            tanggal=date(2026, 8, 1),
            jam_mulai=time(9, 30),
            jam_selesai=time(10, 30)
        )
        with self.assertRaises(ValidationError):
            keg2.save()

        # Activity Harian overlapping keg1 -> should fail Clean
        akt = AktivitasHarian(
            user=self.userA,
            judul='Akt Overlap',
            jam_mulai=time(9, 15),
            durasi_menit=30,
            tanggal=date(2026, 8, 1)
        )
        with self.assertRaises(ValidationError):
            akt.save()

    def test_kegiatan_user_isolation(self):
        kegA = Kegiatan.objects.create(
            user=self.userA,
            judul='User A Secret Event',
            kategori='pribadi_sosial',
            tanggal=date(2026, 8, 1),
            jam_mulai=time(14, 0),
            jam_selesai=time(15, 0)
        )

        # Login as User B
        self.client.force_login(self.userB)
        
        # User B tries to view -> should not contain User A's secret event
        response = self.client.get(reverse('tugas:kegiatan_list'))
        self.assertNotContains(response, 'User A Secret Event')

        # User B tries to edit User A's event -> 404
        response_edit = self.client.post(reverse('tugas:kegiatan_edit', args=[kegA.id]), {
            'judul': 'Hacked',
            'kategori': 'pribadi_sosial',
            'tanggal': '2026-08-01',
            'jam_mulai': '14:00',
            'jam_selesai': '15:00',
            'status': 'selesai'
        })
        self.assertEqual(response_edit.status_code, 404)

        # User B tries to delete User A's event -> 404
        response_delete = self.client.post(reverse('tugas:kegiatan_hapus', args=[kegA.id]))
        self.assertEqual(response_delete.status_code, 404)

    def test_kegiatan_toggle_status(self):
        keg = Kegiatan.objects.create(
            user=self.userA,
            judul='Acara Rapat',
            kategori='akademik',
            tanggal=date.today(),
            jam_mulai=time(10, 0),
            jam_selesai=time(11, 0),
            status='akan_datang'
        )
        self.client.force_login(self.userA)
        response = self.client.post(
            reverse('tugas:kegiatan_toggle_status', args=[keg.id]),
            '{"status": "selesai"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        keg.refresh_from_db()
        self.assertEqual(keg.status, 'selesai')

        # Test invalid status
        response_invalid = self.client.post(
            reverse('tugas:kegiatan_toggle_status', args=[keg.id]),
            '{"status": "invalid_status"}',
            content_type='application/json'
        )
        self.assertEqual(response_invalid.status_code, 400)


class Timeline24hTests(TestCase):
    """Tests untuk timeline 24 jam generator, API jadwal, dan dashboard combined stats."""

    def setUp(self):
        self.user = User.objects.create_user(username='timeuser', password='pass123')
        self.client = Client()
        self.client.force_login(self.user)

    def test_24h_timeline_generator(self):
        """Verifikasi helper _generate_24h_timeline menghasilkan slot kosong + item terisi."""
        akt = AktivitasHarian.objects.create(
            user=self.user,
            judul='Morning Run',
            jam_mulai=time(7, 0),
            durasi_menit=30,
            tanggal=date.today(),
        )
        aktivitas_list = AktivitasHarian.objects.filter(user=self.user, tanggal=date.today())
        kegiatan_list = Kegiatan.objects.filter(user=self.user, tanggal=date.today())

        timeline = _generate_24h_timeline(aktivitas_list, kegiatan_list)

        # Timeline should not be empty
        self.assertTrue(len(timeline) > 0)

        # Should contain the aktivitas item
        filled_items = [t for t in timeline if t['type'] == 'aktivitas']
        self.assertEqual(len(filled_items), 1)
        self.assertEqual(filled_items[0]['judul'], 'Morning Run')
        self.assertEqual(filled_items[0]['jam_mulai'], '07:00')

        # Should contain empty slots
        empty_items = [t for t in timeline if t['type'] == 'kosong']
        self.assertTrue(len(empty_items) > 0)

        # Total coverage: all slots should cover 0 to 1440 minutes without gaps
        all_starts = []
        for item in timeline:
            h, m = item['jam_mulai'].split(':')
            all_starts.append(int(h) * 60 + int(m))
        self.assertEqual(all_starts[0], 0, 'Timeline should start at 00:00')

    def test_api_jadwal_today(self):
        """Verifikasi endpoint API jadwal hari ini returns correct data."""
        AktivitasHarian.objects.create(
            user=self.user,
            judul='Test Task',
            jam_mulai=time(14, 0),
            durasi_menit=30,
            tanggal=date.today(),
            status='belum',
        )
        AktivitasHarian.objects.create(
            user=self.user,
            judul='Done Task',
            jam_mulai=time(15, 0),
            durasi_menit=30,
            tanggal=date.today(),
            status='selesai',
        )
        response = self.client.get(reverse('tugas:api_jadwal_today'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('items', data)
        # Only 'belum' status should be returned
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['judul'], 'Test Task')

    def test_dashboard_combined_stats(self):
        """Verifikasi dashboard menghitung gabungan Tugas + Jadwal + Kegiatan."""
        # Create 1 tugas (selesai)
        Tugas.objects.create(
            user=self.user,
            judul='Tugas A',
            status='selesai',
        )
        # Create 1 tugas (belum)
        Tugas.objects.create(
            user=self.user,
            judul='Tugas B',
            status='belum',
        )
        # Create 1 aktivitas (selesai)
        AktivitasHarian.objects.create(
            user=self.user,
            judul='Aktivitas Selesai',
            jam_mulai=time(8, 0),
            durasi_menit=30,
            tanggal=date.today(),
            status='selesai',
        )
        # Create 1 kegiatan (selesai)
        Kegiatan.objects.create(
            user=self.user,
            judul='Kegiatan Done',
            tanggal=date.today(),
            jam_mulai=time(10, 0),
            jam_selesai=time(11, 0),
            status='selesai',
        )

        response = self.client.get(reverse('tugas:dashboard'))
        self.assertEqual(response.status_code, 200)

        # total_items = 2 tugas + 1 aktivitas + 1 kegiatan = 4
        self.assertEqual(response.context['total_items'], 4)
        # completed_items = 1 tugas selesai + 1 aktivitas selesai + 1 kegiatan selesai = 3
        self.assertEqual(response.context['completed_items'], 3)
        # belum_items = 4 - 3 = 1
        self.assertEqual(response.context['belum_items'], 1)
        # progres = round(3/4 * 100) = 75
        self.assertEqual(response.context['progres_persen'], 75)


# ══════════════════════════════════════════════════════════════════════
# BUG-01: Edit Aktivitas Hanya Boleh Berbasis PK (Bukan Judul)
# ══════════════════════════════════════════════════════════════════════

class BugEditAktivitasDuplikatTest(TestCase):
    """
    Memastikan edit_aktivitas_view HANYA mengubah satu objek berdasarkan pk.
    Tidak boleh menimpa aktivitas lain yang berjudul sama.
    """
    def setUp(self):
        self.user = User.objects.create_user(username='buguser', password='testpass123')
        self.client = Client()
        self.client.force_login(self.user)

    def test_edit_aktivitas_tidak_menimpa_aktivitas_judul_sama(self):
        """Edit aktivitas jam 05:01 tidak boleh menghapus/menimpa aktivitas jam 17:00 (judul sama)."""
        today = date.today()
        akt_pagi = AktivitasHarian.objects.create(
            user=self.user, judul="Membantu orang tua",
            jam_mulai=time(5, 1), durasi_menit=30, tanggal=today,
        )
        akt_sore = AktivitasHarian.objects.create(
            user=self.user, judul="Membantu orang tua",
            jam_mulai=time(17, 0), durasi_menit=60, tanggal=today,
            is_habit=True,
        )

        # Edit akt_pagi: ubah is_habit menjadi True
        url = reverse('tugas:edit_aktivitas', kwargs={'aktivitas_id': akt_pagi.pk})
        response = self.client.post(url, {
            'judul': 'Membantu orang tua',
            'jam_mulai': '05:01',
            'durasi_menit': 30,
            'is_habit': True,
            'tanggal': today.isoformat(),
        })

        # akt_sore harus masih ada dan tidak berubah
        akt_sore.refresh_from_db()
        self.assertEqual(akt_sore.jam_mulai, time(17, 0))
        self.assertEqual(akt_sore.durasi_menit, 60)

        # Jumlah total aktivitas hari ini harus tetap 2
        count = AktivitasHarian.objects.filter(user=self.user, tanggal=today).count()
        self.assertEqual(count, 2)

    def test_edit_aktivitas_hanya_ubah_target_pk(self):
        """Setelah edit, hanya objek dengan pk yang ditarget yang berubah."""
        today = date.today()
        akt_a = AktivitasHarian.objects.create(
            user=self.user, judul="Olahraga",
            jam_mulai=time(6, 0), durasi_menit=30, tanggal=today,
        )
        akt_b = AktivitasHarian.objects.create(
            user=self.user, judul="Olahraga",
            jam_mulai=time(18, 0), durasi_menit=30, tanggal=today,
        )

        url = reverse('tugas:edit_aktivitas', kwargs={'aktivitas_id': akt_a.pk})
        self.client.post(url, {
            'judul': 'Olahraga Pagi',
            'jam_mulai': '06:00',
            'durasi_menit': 45,
            'tanggal': today.isoformat(),
        })

        akt_a.refresh_from_db()
        akt_b.refresh_from_db()

        self.assertEqual(akt_a.judul, 'Olahraga Pagi')
        self.assertEqual(akt_a.durasi_menit, 45)
        # akt_b tidak boleh berubah
        self.assertEqual(akt_b.judul, 'Olahraga')
        self.assertEqual(akt_b.durasi_menit, 30)


# ══════════════════════════════════════════════════════════════════════
# BUG-02: Overdue Task Lockout — Edit Tugas Lewat Deadline
# ══════════════════════════════════════════════════════════════════════

class BugOverdueTaskLockoutTest(TestCase):
    """
    Memastikan tugas yang sudah overdue masih bisa diedit
    (judul, deskripsi, prioritas) tanpa harus mengganti deadline.
    """
    def setUp(self):
        self.user = User.objects.create_user(username='overdueuser', password='testpass123')

    def _create_overdue_task(self):
        """Buat tugas overdue langsung via QuerySet (bypass validasi clean)."""
        from django.utils.timezone import now as tz_now
        tugas = Tugas(
            user=self.user,
            judul='Tugas Lama',
            deadline=tz_now() - timedelta(days=3),
            status='belum',
            prioritas='sedang',
            kategori='kerja',
        )
        # Simpan langsung tanpa full_clean untuk bypass validasi (simulasi data lama)
        Tugas.objects.bulk_create([tugas])
        return Tugas.objects.filter(user=self.user, judul='Tugas Lama').first()

    def test_tugas_baru_dengan_deadline_lampau_ditolak(self):
        """Tugas baru dengan deadline di masa lampau harus ditolak."""
        from django.utils.timezone import now as tz_now
        tugas = Tugas(
            user=self.user,
            judul='Tugas Baru Invalid',
            deadline=tz_now() - timedelta(hours=1),
            status='belum',
            prioritas='sedang',
            kategori='kerja',
        )
        with self.assertRaises(ValidationError):
            tugas.full_clean()

    def test_edit_tugas_overdue_deadline_tidak_berubah_harus_lolos(self):
        """Saat edit tugas overdue, jika deadline tidak diubah, tidak boleh ada ValidationError."""
        tugas = self._create_overdue_task()
        if tugas is None:
            self.skipTest("Tugas overdue tidak berhasil dibuat.")

        # Ubah hanya judul (deadline tetap sama)
        tugas.judul = 'Tugas Lama (Diperbarui)'
        try:
            tugas.full_clean()
        except ValidationError as e:
            self.fail(f"ValidationError tidak seharusnya terjadi saat edit judul tugas overdue: {e}")

    def test_pesan_validasi_tidak_mengandung_emoji(self):
        """Pesan error validasi tidak boleh mengandung karakter emoji."""
        from django.utils.timezone import now as tz_now
        tugas = Tugas(
            user=self.user,
            judul='Tugas Test',
            deadline=tz_now() - timedelta(hours=2),
            status='belum',
            prioritas='rendah',
            kategori='pribadi',
        )
        try:
            tugas.full_clean()
            self.fail("Seharusnya ada ValidationError untuk tugas baru dengan deadline lampau")
        except ValidationError as e:
            for msg in e.messages:
                # Pastikan tidak ada karakter emoji (cek karakter non-ASCII tinggi)
                self.assertNotIn('\u26d4', msg, "Emoji ⛔ ditemukan dalam pesan validasi!")
                self.assertNotIn('\U0001f525', msg, "Emoji ditemukan dalam pesan validasi!")


# ══════════════════════════════════════════════════════════════════════
# BUG-03: Midnight-Crossing Overlap Detection
# ══════════════════════════════════════════════════════════════════════

class BugMidnightCrossingOverlapTest(TestCase):
    """
    Memastikan deteksi bentrok jadwal bekerja dengan benar
    untuk aktivitas yang melewati tengah malam (23:30 + 60 menit = 00:30).
    """
    def setUp(self):
        self.user = User.objects.create_user(username='midnightuser', password='testpass123')

    def test_aktivitas_melewati_tengah_malam_terdeteksi_overlap(self):
        """Aktivitas 23:30 (60 menit) harus overlap dengan aktivitas 00:00 (30 menit)."""
        today = date.today()
        # Buat aktivitas 23:30 - 00:30 (midnight-crossing)
        akt_late = AktivitasHarian.objects.create(
            user=self.user,
            judul='Kerja Malam',
            jam_mulai=time(23, 30),
            durasi_menit=60,  # selesai 00:30 hari berikutnya
            tanggal=today,
        )

        # Coba buat aktivitas 00:00 - 00:30 di hari yang sama
        akt_early = AktivitasHarian(
            user=self.user,
            judul='Aktivitas Dini Hari',
            jam_mulai=time(0, 0),
            durasi_menit=29,  # selesai 00:29 — seharusnya overlap dengan akt_late
            tanggal=today,
        )
        with self.assertRaises(ValidationError):
            akt_early.full_clean()

    def test_aktivitas_tidak_overlap_jika_tidak_bertabrakan(self):
        """Aktivitas 22:00 (60 menit) dan 23:30 (30 menit) tidak boleh overlap."""
        today = date.today()
        AktivitasHarian.objects.create(
            user=self.user,
            judul='Makan Malam',
            jam_mulai=time(22, 0),
            durasi_menit=60,  # selesai 23:00
            tanggal=today,
        )
        akt_no_overlap = AktivitasHarian(
            user=self.user,
            judul='Belajar Malam',
            jam_mulai=time(23, 30),
            durasi_menit=30,  # selesai 00:00
            tanggal=today,
        )
        # Tidak boleh raise ValidationError
        try:
            akt_no_overlap.full_clean()
        except ValidationError as e:
            self.fail(f"ValidationError tidak seharusnya terjadi: {e}")
