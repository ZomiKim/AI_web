import { useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Container from '@mui/material/Container';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

const checklist = [
  'React + Vite 개발 서버 실행',
  'MUI ThemeProvider 테마 적용',
  'CssBaseline 기본 스타일 초기화',
];

function App() {
  const [count, setCount] = useState(0);

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Card elevation={2}>
        <CardContent>
          <Stack spacing={3}>
            <Box>
              <Typography variant="h4" component="h1" gutterBottom>
                Lecture 1
              </Typography>
              <Typography color="text.secondary">
                React + Vite + MUI 개발 환경이 정상적으로 실행되었습니다.
              </Typography>
            </Box>

            <Box component="ul" sx={{ m: 0, pl: 3 }}>
              {checklist.map((item) => (
                <Typography component="li" key={item}>
                  {item}
                </Typography>
              ))}
            </Box>

            <Stack direction="row" spacing={2} alignItems="center">
              <Button variant="contained" onClick={() => setCount((c) => c + 1)}>
                클릭 수: {count}
              </Button>
              <Button variant="outlined" color="secondary" onClick={() => setCount(0)}>
                초기화
              </Button>
            </Stack>
          </Stack>
        </CardContent>
      </Card>
    </Container>
  );
}

export default App;
