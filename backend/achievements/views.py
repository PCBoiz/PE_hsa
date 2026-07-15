"""Port routes/achievements.py."""
from rest_framework.response import Response
from rest_framework.views import APIView

from common.db import q


class AchievementsView(APIView):
    def get(self, request):
        rows = q('''SELECT a.id, a.code, a.name, a.description, a.icon,
                           a.condition_type, a.condition_value, ua.awarded_at
                    FROM achievements a
                    LEFT JOIN user_achievements ua
                           ON ua.achievement_id = a.id AND ua.user_id = %s
                    ORDER BY a.id''', (request.user.id,))
        result = []
        for d in rows:
            d['conditionType'] = d.pop('condition_type')
            d['conditionValue'] = d.pop('condition_value')
            awarded_at = d.pop('awarded_at')
            d['awardedAt'] = awarded_at.isoformat() if awarded_at else None
            d['unlocked'] = awarded_at is not None
            result.append(d)

        return Response({
            'achievements': result,
            'unlockedCount': sum(1 for d in result if d['unlocked']),
            'totalCount': len(result),
        })
