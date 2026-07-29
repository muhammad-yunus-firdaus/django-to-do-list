from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date, time, timedelta

from .models import Tugas, Subtask, AktivitasHarian, EvaluasiMingguan
from .views import _get_week_range, _get_weekly_stats, _get_next_free_slot


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
        t1.created_at = start + timedelta(hours=12)
        t1.save()

        t2 = Tugas.objects.create(
            user=self.user, judul='Tugas 2', prioritas='sedang', kategori='kerja', status='belum'
        )
        t2.created_at = start + timedelta(days=1)
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
